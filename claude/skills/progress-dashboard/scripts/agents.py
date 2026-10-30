"""Which Claude Code sessions on this host are waiting for the user.

Every hook event rewrites one small JSON file per session under
~/.local/state/progress-dashboard/agents/. Works for any session on the host,
inside herdr or not, and for repos that never ran `progress.py init`.
Prompt text and tool inputs are never stored: the hub shows these on the LAN.
"""

import contextlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
MAX_DETAIL = 60


def state_dir():
    override = os.environ.get("PROGRESS_AGENTS_DIR")
    if override:
        return Path(override)
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state) / "progress-dashboard" / "agents"


def _proc_start(pid):
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    # Field 22 (starttime) follows the parenthesised comm, which may contain spaces.
    return stat.rsplit(")", 1)[1].split()[19]


def claude_pid():
    """The claude process that ran this hook (hooks are spawned through a shell)."""
    pid = os.getppid()
    for _ in range(8):
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            ppid = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return None
        if re.search(r"(^|/)claude(\s|$)", cmd) or "claude-code" in cmd or "@anthropic-ai/claude" in cmd:
            return pid
        if ppid <= 1:
            return None
        pid = ppid
    return None


def _git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=1.5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _atomic_write(path, obj):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def _short(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:MAX_DETAIL] + ("…" if len(text) > MAX_DETAIL else "")


def transition(event, payload):
    """(state, detail) for a hook event, or None when the event changes nothing."""
    if event == "SessionStart":
        return "idle", "起動直後"
    if event == "UserPromptSubmit":
        return "working", ""
    if event == "PermissionRequest":
        return "blocked", f"{_short(payload.get('tool_name'))} の承認"
    if event == "PreToolUse" and payload.get("tool_name") == "AskUserQuestion":
        qs = (payload.get("tool_input") or {}).get("questions") or [{}]
        return "blocked", "質問: " + _short(qs[0].get("header") or qs[0].get("question") or "")
    if event == "PostToolUse":
        return "working", ""
    if event == "Notification":
        kind = payload.get("notification_type") or ""
        if kind == "idle_prompt":
            return "idle", "応答後に入力なし"
        if kind in ("permission_prompt", "elicitation_dialog", "elicitation_url_dialog"):
            return "blocked", "入力待ち"
        return None
    if event == "Stop":
        return None if payload.get("stop_hook_active") else ("done", "応答を終えた")
    if event == "StopFailure":
        return "blocked", "エラーで停止: " + _short(payload.get("error"))
    return None


def record(payload):
    """Best effort; callers swallow exceptions so the session is never affected."""
    sid = payload.get("session_id") or ""
    event = payload.get("hook_event_name") or ""
    if not SESSION_ID_RE.match(sid) or payload.get("agent_id"):
        return
    d = state_dir()
    path = d / f"{sid}.json"
    marker = d / f"{sid}.waiting"
    if event == "SessionEnd":
        for p in (path, marker):
            with contextlib.suppress(FileNotFoundError):
                p.unlink()
        return
    t = transition(event, payload)
    if t is None:
        return
    state, detail = t
    d.mkdir(parents=True, exist_ok=True)
    try:
        prev = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}
    if event == "PostToolUse" and prev.get("state") != "blocked":
        return
    cwd = payload.get("cwd") or os.getcwd()
    entry = dict(prev)
    if not prev or prev.get("cwd") != cwd:
        top = _git(cwd, "rev-parse", "--show-toplevel")
        entry.update({"cwd": cwd, "root": top or cwd, "branch": _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")})
    if not prev.get("pid"):
        pid = claude_pid()
        entry.update({"pid": pid, "pid_start": _proc_start(pid) if pid else None})
    entry.update({"session_id": sid, "state": state, "detail": detail,
                  "herdr_pane": os.environ.get("HERDR_PANE_ID") or prev.get("herdr_pane")})
    if prev.get("state") != state or prev.get("detail") != detail:
        entry["since"] = time.time()
    entry["seen"] = time.time()
    _atomic_write(path, entry)
    # PostToolUse checks for this marker in bash first, so Python only runs while someone waits.
    if state == "blocked":
        marker.touch()
    else:
        with contextlib.suppress(FileNotFoundError):
            marker.unlink()


def alive(entry):
    pid = entry.get("pid")
    if not pid:
        return True  # cannot tell; keep it rather than hide a waiting session
    return _proc_start(pid) is not None and _proc_start(pid) == entry.get("pid_start")


def list_agents():
    """Live sessions; files of sessions that died without SessionEnd are removed."""
    out = []
    d = state_dir()
    if not d.is_dir():
        return out
    for f in d.glob("*.json"):
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not alive(entry):
            for p in (f, f.with_suffix(".waiting")):
                with contextlib.suppress(FileNotFoundError):
                    p.unlink()
            continue
        out.append(entry)
    return out
