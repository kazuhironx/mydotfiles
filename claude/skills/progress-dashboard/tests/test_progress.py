"""Run: python3 -m unittest discover -s claude/skills/progress-dashboard/tests"""

import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "progress.py"
SERVE = SCRIPT.with_name("serve.py")
# Keep test projects out of the real ~/.local/state registry the hub serves.
_REGISTRY_DIR = tempfile.TemporaryDirectory()
os.environ["PROGRESS_REGISTRY"] = str(Path(_REGISTRY_DIR.name) / "projects.json")
os.environ["PROGRESS_AGENTS_DIR"] = str(Path(_REGISTRY_DIR.name) / "agents")


def run(cwd, *args, stdin=None, env=None):
    full_env = dict(os.environ, **(env or {}))
    full_env.pop("PROGRESS_SESSION_ID", None)
    full_env.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, input=stdin,
                          capture_output=True, text=True, env=full_env, timeout=30)


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class ProgressTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "-q", "--allow-empty", "-m", "init")
        self.assertEqual(run(self.root, "init", "--goal", "g").returncode, 0)
        self.dd = self.root / ".claude" / "dashboard"

    def tearDown(self):
        self.tmp.cleanup()

    def status(self):
        return json.loads((self.dd / "status.json").read_text())

    def hook(self, event, payload, env=None):
        r = run(self.root, "hook", event, stdin=json.dumps(payload), env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_done_requires_evidence(self):
        run(self.root, "task", "add", "x")
        r = run(self.root, "task", "set", "T1", "done")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.status()["tasks"][0]["status"], "todo")
        self.assertEqual(run(self.root, "task", "set", "T1", "done", "--evidence", "ran it").returncode, 0)
        self.assertEqual(self.status()["tasks"][0]["status"], "done")

    def test_blocked_task_opens_and_closes_its_blocker(self):
        self.assertEqual(run(self.root, "task", "add", "x", "--status", "blocked").returncode, 1)
        run(self.root, "task", "add", "x", "--status", "blocked", "--note", "waiting on HW")
        b = self.status()["blockers"]
        self.assertEqual((len(b), b[0]["task"], b[0]["resolved_at"]), (1, "T1", None))
        run(self.root, "task", "set", "T1", "done", "--evidence", "HW arrived, test passed")
        b = self.status()["blockers"][0]
        self.assertIsNotNone(b["resolved_at"])
        self.assertEqual(b["resolution"], "HW arrived, test passed")

    def test_concurrent_writers_keep_every_update(self):
        n = 24
        with ThreadPoolExecutor(max_workers=12) as ex:
            results = list(ex.map(lambda i: run(self.root, "task", "add", f"t{i}"), range(n)))
        self.assertTrue(all(r.returncode == 0 for r in results), [r.stderr for r in results])
        tasks = self.status()["tasks"]
        self.assertEqual(len(tasks), n)
        self.assertEqual(len({t["id"] for t in tasks}), n)

    def test_killed_writer_leaves_previous_file_intact(self):
        run(self.root, "task", "add", "before")
        # Hold the lock, then SIGKILL a writer waiting on it: the file must stay valid.
        holder = subprocess.Popen([sys.executable, "-c", (
            "import fcntl,os,time,sys;fd=os.open(sys.argv[1],os.O_RDWR);"
            "fcntl.flock(fd,fcntl.LOCK_EX);print('locked',flush=True);time.sleep(30)"),
            str(self.dd / ".lock")], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(holder.stdout.readline().strip(), "locked")
            writer = subprocess.Popen([sys.executable, str(SCRIPT), "task", "add", "during"], cwd=self.root,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.3)
            writer.send_signal(signal.SIGKILL)
            writer.wait()
        finally:
            holder.kill()
            holder.wait()
            holder.stdout.close()
        self.assertEqual([t["title"] for t in self.status()["tasks"]], ["before"])
        self.assertEqual(list(self.dd.glob("*.tmp")), [])

    def test_random_sigkill_never_corrupts(self):
        procs = []
        for i in range(30):
            p = subprocess.Popen([sys.executable, str(SCRIPT), "task", "add", f"k{i}"], cwd=self.root,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            procs.append(p)
            time.sleep(0.005 * (i % 7))
            if i % 2:
                p.send_signal(signal.SIGKILL)
        for p in procs:
            p.wait()
        st = self.status()
        ids = [t["id"] for t in st["tasks"]]
        self.assertEqual(len(ids), len(set(ids)))
        json.loads((self.dd / "decisions.json").read_text())
        # Temp files orphaned by SIGKILL are swept at the next SessionStart.
        for t in self.dd.glob("*.tmp"):
            os.utime(t, (0, 0))
        self.hook("session-start", {"session_id": "s1", "source": "startup", "cwd": str(self.root)})
        self.assertEqual(list(self.dd.glob("*.tmp")), [])

    def test_lock_timeout_fails_cli_without_damage(self):
        holder = subprocess.Popen([sys.executable, "-c", (
            "import fcntl,os,time,sys;fd=os.open(sys.argv[1],os.O_RDWR);"
            "fcntl.flock(fd,fcntl.LOCK_EX);print('locked',flush=True);time.sleep(30)"),
            str(self.dd / ".lock")], stdout=subprocess.PIPE, text=True)
        try:
            holder.stdout.readline()
            r = run(self.root, "task", "add", "x")
            self.assertEqual(r.returncode, 1)
            self.assertIn("lock busy", r.stderr)
            # Hooks swallow the same failure and log it.
            self.hook("session-end", {"session_id": "s1", "reason": "other", "cwd": str(self.root)})
            self.assertIn("lock busy", (self.dd / "hook.log").read_text())
        finally:
            holder.kill()
            holder.wait()
            holder.stdout.close()

    def test_corrupt_json_is_never_overwritten(self):
        (self.dd / "status.json").write_text("{broken")
        r = run(self.root, "task", "add", "x")
        self.assertEqual(r.returncode, 1)
        self.hook("session-end", {"session_id": "s1", "reason": "other", "cwd": str(self.root)})
        self.assertEqual((self.dd / "status.json").read_text(), "{broken")
        self.assertIn("refusing to overwrite", (self.dd / "hook.log").read_text())

    def test_session_lifecycle_and_crash_recovery(self):
        env_file = self.root / "envfile"
        r = self.hook("session-start", {"session_id": "aaa", "source": "startup", "cwd": str(self.root)},
                      env={"CLAUDE_ENV_FILE": str(env_file)})
        self.assertIn("[progress-dashboard]", r.stdout)
        self.assertLessEqual(len(r.stdout.splitlines()), 15)
        self.assertIn("export PROGRESS_SESSION_ID=aaa", env_file.read_text())
        # A parallel session that answered recently stays open.
        self.hook("session-start", {"session_id": "bbb", "source": "startup", "cwd": str(self.root)})
        s = {x["id"]: x for x in self.status()["sessions"]}
        self.assertIsNone(s["aaa"]["ended_at"])
        # Session "aaa" died without SessionEnd and went silent; the next start closes it.
        st = self.status()
        for x in st["sessions"]:
            if x["id"] == "aaa":
                x["last_seen_at"] = "2000-01-01T00:00:00+00:00"
        (self.dd / "status.json").write_text(json.dumps(st))
        self.hook("session-start", {"session_id": "bbb", "source": "resume", "cwd": str(self.root)})
        s = {x["id"]: x for x in self.status()["sessions"]}
        self.assertEqual(s["aaa"]["end_reason"], "missing")
        self.assertIsNone(s["bbb"]["ended_at"])
        # If "aaa" was actually alive, its next Stop reopens it.
        self.hook("stop", {"session_id": "aaa", "stop_hook_active": False, "cwd": str(self.root)})
        s = {x["id"]: x for x in self.status()["sessions"]}
        self.assertIsNone(s["aaa"]["ended_at"])
        # Commit during the session, then end it.
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "-q", "--allow-empty", "-m", "feat: work done in bbb")
        before = (self.dd / "dashboard.html").stat().st_mtime_ns
        time.sleep(0.01)
        self.hook("session-end", {"session_id": "bbb", "reason": "prompt_input_exit", "cwd": str(self.root)})
        s = {x["id"]: x for x in self.status()["sessions"]}
        self.assertEqual(s["bbb"]["end_reason"], "prompt_input_exit")
        self.assertEqual(len(s["bbb"]["commits"]), 1)
        self.assertGreater((self.dd / "dashboard.html").stat().st_mtime_ns, before)
        self.assertIn("feat: work done in bbb", (self.dd / "dashboard.html").read_text())

    def test_stop_writes_only_when_needed(self):
        self.hook("session-start", {"session_id": "s1", "source": "startup", "cwd": str(self.root)})
        m0 = (self.dd / "status.json").stat().st_mtime_ns
        self.hook("stop", {"session_id": "s1", "stop_hook_active": False, "cwd": str(self.root)})
        self.assertEqual((self.dd / "status.json").stat().st_mtime_ns, m0, "idle Stop must not write")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "-q", "--allow-empty", "-m", "c2")
        self.hook("stop", {"session_id": "s1", "stop_hook_active": False, "cwd": str(self.root)})
        self.assertNotEqual((self.dd / "status.json").stat().st_mtime_ns, m0)

    def test_stop_hook_active_is_noop_and_silent(self):
        run(self.root, "task", "add", "x")
        (self.dd / "dashboard.html").unlink()
        r = self.hook("stop", {"session_id": "s1", "stop_hook_active": True, "cwd": str(self.root)})
        self.assertEqual(r.stdout, "")
        self.assertFalse((self.dd / "dashboard.html").exists())

    def test_cli_update_rerenders_html(self):
        run(self.root, "task", "add", "visible-task-title")
        self.assertIn("visible-task-title", (self.dd / "dashboard.html").read_text())

    def test_projects_without_dashboard_are_untouched(self):
        with tempfile.TemporaryDirectory() as other:
            for ev in ("session-start", "stop", "session-end"):
                r = run(other, "hook", ev, stdin=json.dumps({"session_id": "x", "cwd": other}),
                        env={"CLAUDE_PROJECT_DIR": other})
                self.assertEqual((r.returncode, r.stdout), (0, ""))
            self.assertEqual(os.listdir(other), [])

    def test_html_escapes_and_redacts(self):
        run(self.root, "task", "add", '<img src=x onerror="alert(1)"> & "q"')
        run(self.root, "decision", "add", "--title", "<b>t</b>", "--decision", "d",
            "--reason", "password=hunter2 ghp_0123456789abcdefghijABCDEFGHIJ")
        page = (self.dd / "dashboard.html").read_text()
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<b>t</b>", page)
        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", page)
        self.assertNotIn("hunter2", page)
        self.assertNotIn("ghp_0123", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("hunter2", (self.dd / "decisions.json").read_text())

    def test_stale_pass_is_flagged_after_new_commit(self):
        run(self.root, "test", "unit", "pass")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "-q", "--allow-empty", "-m", "c2")
        run(self.root, "render")
        self.assertIn("要再実行", (self.dd / "dashboard.html").read_text())

    def test_manual_summary_does_not_look_like_a_crash(self):
        run(self.root, "summary", "did things")
        self.hook("session-start", {"session_id": "s1", "source": "startup", "cwd": str(self.root)})
        s = {x["id"]: x for x in self.status()["sessions"]}
        self.assertEqual(s["manual"]["end_reason"], "manual")

    def test_subagent_events_are_ignored(self):
        m0 = (self.dd / "status.json").stat().st_mtime_ns
        self.hook("session-end", {"session_id": "s1", "agent_id": "a1", "cwd": str(self.root)})
        self.assertEqual((self.dd / "status.json").stat().st_mtime_ns, m0)


if __name__ == "__main__":
    unittest.main()


class HubTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        os.environ["PROGRESS_REGISTRY"] = str(base / "registry.json")
        self.roots = []
        for sub in ("a/app", "b/app"):  # same basename, different repos
            r = base / sub
            r.mkdir(parents=True)
            git(r, "init", "-q")
            self.assertEqual(run(r, "init", "--goal", f"goal-{sub}").returncode, 0)
            self.roots.append(r)
        run(self.roots[0], "blocker", "add", "stuck-here")
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.proc = subprocess.Popen([sys.executable, str(SERVE), "--bind", "127.0.0.1", "--port", str(self.port)],
                                     stderr=subprocess.PIPE, text=True)
        self.assertIn("serving", self.proc.stderr.readline())

    def tearDown(self):
        self.proc.kill()
        self.proc.wait()
        self.proc.stderr.close()
        self.tmp.cleanup()

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        r = conn.getresponse()
        body = r.read().decode()
        conn.close()
        return r.status, body

    def test_registry_slugs_are_unique_for_same_basename(self):
        reg = json.loads(Path(os.environ["PROGRESS_REGISTRY"]).read_text())
        slugs = [p["slug"] for p in reg["projects"]]
        self.assertEqual(len(slugs), 2)
        self.assertEqual(len(set(slugs)), 2)
        run(self.roots[0], "render")
        self.assertEqual(len(json.loads(Path(os.environ["PROGRESS_REGISTRY"]).read_text())["projects"]), 2)

    def test_index_lists_projects_problems_first(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("goal-a/app", body)
        self.assertIn("goal-b/app", body)
        self.assertLess(body.index("goal-a/app"), body.index("goal-b/app"))
        self.assertIn("対応が必要な問題があります", body)

    def test_project_page_and_private_files(self):
        reg = json.loads(Path(os.environ["PROGRESS_REGISTRY"]).read_text())
        slug = reg["projects"][0]["slug"]
        status, body = self.get(f"/p/{slug}/")
        self.assertEqual(status, 200)
        self.assertIn("全プロジェクト", body)
        self.assertIn("stuck-here", body)
        for path in (f"/p/{slug}/status.json", f"/p/{slug}/../../etc/passwd", "/p/nope/",
                     "/status.json", "/../", "/p/../registry.json"):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_stale_page_is_rerendered_on_request(self):
        slug = json.loads(Path(os.environ["PROGRESS_REGISTRY"]).read_text())["projects"][0]["slug"]
        dd = self.roots[0] / ".claude" / "dashboard"
        st = json.loads((dd / "status.json").read_text())
        st["goal"] = "changed-outside-any-session"
        time.sleep(0.05)
        (dd / "status.json").write_text(json.dumps(st))
        self.assertIn("changed-outside-any-session", self.get(f"/p/{slug}/")[1])

    def test_help_page_is_linked_from_index_and_projects(self):
        status, body = self.get("/help")
        self.assertEqual(status, 200)
        self.assertIn("unregister", body)
        self.assertIn('href="/help"', self.get("/")[1])
        slug = json.loads(Path(os.environ["PROGRESS_REGISTRY"]).read_text())["projects"][0]["slug"]
        self.assertIn('href="/help"', self.get(f"/p/{slug}/")[1])

    def test_removed_project_drops_out(self):
        import shutil
        shutil.rmtree(self.roots[1] / ".claude")
        self.assertNotIn("goal-b/app", self.get("/")[1])


REMAINING = """# 今の残件

| # | 項目 | 扱い |
|---|---|---|
| P1 | ベンダに聞く | **Action Item** |
| P2 | Pod で動かす | **10-09 済 (14/14 応答)** |

### A. 電源

| # | 項目 | 中身 | 重さ |
|---|---|---|---|
| A1 | **ログの収集** | **済 (10-08)**: 問題なし | 小 |
| ~~A5~~ | ~~古いドライバ~~ | やらない (10-08、ユーザ判断): 理由 | — |
| A6 | ~~**旧サービスを外す**~~ → **10-20 済** (理由) | x | 中 |
| A7 | ~~消しただけ~~ | 何も書いていない | 小 |
| A8 | 途中まで進んだ | 10-09 実装・実機で確認 | 中 |

### 実機を使う残タスク

| 分類 | 項目 | 備考 |
|---|---|---|
| 電源 | A6 の重複 | 無視される |

### B. 出社・ベンダが要るもの

| # | 項目 | 待ち |
|---|---|---|
| B1 | 電源ボタンの確認 | 出社 |
| ~~B2~~ | ~~回線の手配~~ | 10-21 済 |
"""

DECISIONS = """# メモ

## 決めたこと (10-17、ユーザ)

| # | 項目 | 決定 |
|---|---|---|
| 1 | ブランチの運用 | main に直接コミットする |

## 別の節

| # | 項目 | 決定 |
|---|---|---|
| 9 | 拾わない | x |
"""


class SourcedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        (self.root / "notes").mkdir()
        (self.root / "notes" / "remaining.md").write_text(REMAINING)
        (self.root / "notes" / "2026-10-17-dev-infra.md").write_text(DECISIONS)
        r = run(self.root, "init", "--tasks-from", "notes/remaining.md", "--decisions-from", "notes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.dd = self.root / ".claude" / "dashboard"

    def tearDown(self):
        self.tmp.cleanup()

    def tasks(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import sources
        return {t["id"]: t for t in sources.read_backlog(self.root / "notes" / "remaining.md")}

    def test_states_come_only_from_explicit_markers(self):
        t = self.tasks()
        self.assertEqual({k: v["status"] for k, v in t.items()}, {
            "P1": "open", "P2": "done", "A1": "done", "A5": "dropped", "A6": "done",
            "A7": "closed", "A8": "open", "B1": "waiting", "B2": "done"})
        self.assertIn("済 (10-08)", t["A1"]["evidence"])
        self.assertIn("10-20 済", t["A6"]["evidence"])
        self.assertIn("実装・実機で確認", t["A8"]["note"])

    def test_cli_refuses_to_own_tasks_and_decisions(self):
        for args in (("task", "add", "x"), ("blocker", "add", "x"), ("next", "add", "x"),
                     ("decision", "add", "--title", "t", "--decision", "d", "--reason", "r")):
            r = run(self.root, *args)
            self.assertEqual(r.returncode, 1, args)
            self.assertIn("source of truth", r.stderr)
        self.assertEqual(run(self.root, "test", "unit", "pass").returncode, 0)

    def test_dashboard_shows_backlog_and_note_decisions(self):
        page = (self.dd / "dashboard.html").read_text()
        for text in ("Pod で動かす", "電源ボタンの確認", "外部待ち", "main に直接コミットする",
                     "notes/2026-10-17-dev-infra.md「決めたこと (10-17、ユーザ)」"):
            self.assertIn(text, page)
        self.assertNotIn("拾わない", page)
        self.assertNotIn("A6 の重複", page)
        brief = run(self.root, "show").stdout
        self.assertIn("外部待ち B1", brief)
        self.assertIn("正本は notes/remaining.md", brief)

    def test_editing_the_source_rerenders_on_stop(self):
        self.hook_stop()
        time.sleep(0.05)
        path = self.root / "notes" / "remaining.md"
        path.write_text(path.read_text().replace("| P1 | ベンダに聞く |", "| P1 | ~~ベンダに聞く~~ 10-30 済 |"))
        self.hook_stop()
        self.assertIn("10-30 済", (self.dd / "dashboard.html").read_text())

    def hook_stop(self):
        r = run(self.root, "hook", "stop", stdin=json.dumps({"session_id": "s1", "cwd": str(self.root)}))
        self.assertEqual(r.returncode, 0, r.stderr)


class AgentStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "agents"
        os.environ["PROGRESS_AGENTS_DIR"] = str(self.dir)
        self.cwd = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def send(self, event, sid="s1", hook="agent", **extra):
        payload = {"session_id": sid, "hook_event_name": event, "cwd": self.cwd, **extra}
        r = run(self.cwd, "hook", hook, stdin=json.dumps(payload))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def state(self, sid="s1"):
        return json.loads((self.dir / f"{sid}.json").read_text())

    def test_lifecycle_and_no_prompt_text_stored(self):
        self.send("SessionStart", hook="session-start")
        self.assertEqual(self.state()["state"], "idle")
        self.send("UserPromptSubmit", prompt="SECRET-PROMPT-TEXT")
        self.assertEqual(self.state()["state"], "working")
        self.send("PermissionRequest", tool_name="Bash", tool_input={"command": "echo SECRET-CMD"})
        st = self.state()
        self.assertEqual((st["state"], st["detail"]), ("blocked", "Bash の承認"))
        self.assertTrue((self.dir / "s1.waiting").exists())
        self.send("PostToolUse", tool_name="Bash")
        self.assertEqual(self.state()["state"], "working")
        self.assertFalse((self.dir / "s1.waiting").exists())
        self.send("PreToolUse", tool_name="AskUserQuestion",
                  tool_input={"questions": [{"header": "公開範囲", "question": "q"}]})
        self.assertEqual(self.state()["detail"], "質問: 公開範囲")
        self.send("Stop", hook="stop", stop_hook_active=False)
        self.assertEqual(self.state()["state"], "done")
        self.send("Notification", notification_type="idle_prompt")
        self.assertEqual(self.state()["state"], "idle")
        raw = (self.dir / "s1.json").read_text()
        self.assertNotIn("SECRET", raw)
        self.send("SessionEnd", hook="session-end", reason="other")
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_post_tool_use_does_not_touch_working_sessions(self):
        self.send("UserPromptSubmit")
        m0 = (self.dir / "s1.json").stat().st_mtime_ns
        self.send("PostToolUse", tool_name="Read")
        self.assertEqual((self.dir / "s1.json").stat().st_mtime_ns, m0)

    def test_dead_sessions_are_dropped_and_index_shows_waiting(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import agents
        import render
        self.dir.mkdir(parents=True)
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        (self.dir / "gone.json").write_text(json.dumps({"session_id": "gone", "state": "blocked",
                                                         "pid": dead.pid, "pid_start": "1"}))
        me = os.getpid()
        (self.dir / "live.json").write_text(json.dumps({
            "session_id": "live", "state": "blocked", "detail": "Bash の承認", "root": "/x/app",
            "pid": me, "pid_start": agents._proc_start(me), "since": time.time() - 120}))
        listed = agents.list_agents()
        self.assertEqual([a["session_id"] for a in listed], ["live"])
        self.assertFalse((self.dir / "gone.json").exists())
        page = render.render_index([], "h", listed)
        self.assertIn("あなたの対応待ち", page)
        self.assertIn("Bash の承認", page)
        self.assertIn("2分前", page)
        self.assertIn('http-equiv="refresh"', page)
        self.assertIn("%23d03b3b", page)  # favicon turns red while a session is blocked
