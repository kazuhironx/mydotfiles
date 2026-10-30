"""Render status.json + decisions.json into a self-contained dashboard.html.

No JavaScript and no external resources: the CSP meta blocks anything that is not
inline CSS or a data: image, so a stray value can never load or run something.
"""

import datetime as dt
import html
from pathlib import Path

from progress import redact

STATUS = {
    # key: (label, icon, css class)
    "blocked": ("ブロック中", "stop", "st-blocked"),
    "doing": ("進行中", "play", "st-doing"),
    "unverified": ("未検証", "alert", "st-unverified"),
    "todo": ("未着手", "circle", "st-todo"),
    "done": ("完了", "check", "st-done"),
    "dropped": ("中止", "minus", "st-dropped"),
    # Only from a project's own backlog (sources.py); never set by the CLI.
    "open": ("未完", "circle", "st-todo"),
    "waiting": ("外部待ち", "pause", "st-waiting"),
    "closed": ("閉じた", "minus", "st-dropped"),
}
HIDDEN = ("dropped", "closed")
# One 12px grid, 1.6 stroke, currentColor: inline so the CSP needs no img-src.
ICON_PATHS = {
    "check": '<path d="M2.5 6.5l2.3 2.3L9.5 3.5"/>',
    "alert": '<path d="M6 1.8L10.8 10H1.2z"/><path d="M6 5v2.2"/><path d="M6 8.6v.1"/>',
    "stop": '<rect x="2.2" y="2.2" width="7.6" height="7.6" rx="1"/><path d="M4.3 4.3l3.4 3.4M7.7 4.3L4.3 7.7"/>',
    "play": '<path d="M3.5 2.2v7.6L9.6 6z"/>',
    "circle": '<circle cx="6" cy="6" r="3.8"/>',
    "minus": '<path d="M2.5 6h7"/>',
    "pause": '<path d="M4.3 2.8v6.4M7.7 2.8v6.4"/>',
}


def icon(name):
    return ('<svg class="ic" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICON_PATHS[name]}</svg>')
BAR_ORDER = ("done", "unverified", "doing", "waiting", "blocked", "open", "todo")
TABLE_ORDER = ("blocked", "waiting", "doing", "unverified", "open", "todo", "done")
END_REASON = {
    "clear": "/clear で終了",
    "resume": "別セッションへ切替",
    "logout": "ログアウト",
    "prompt_input_exit": "ユーザーが終了",
    "bypass_permissions_disabled": "権限モード変更で終了",
    "other": "終了",
    "missing": "終了記録なし（異常終了の可能性）",
    "manual": "Hook 外での手動記録",
}
EVENT_KIND = {"task": "タスク", "test": "テスト", "decision": "判断", "blocker": "ブロッカー",
              "pivot": "方針変更", "note": "メモ", "goal": "目標", "init": "初期化",
              "recover": "復旧"}

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;
--muted:#6b6a65;--line:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10);
--good:#0ca30c;--good-ink:#006300;--warn:#fab219;--warn-ink:#7a5300;--crit:#d03b3b;--crit-ink:#a32020;
--doing:#2a78d6;--doing-ink:#1d5aa6;--todo:#c3c2b7;--crit-wash:#fbeaea;--warn-wash:#fdf4e0}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink-2:#c3c2b7;--muted:#9a9890;--line:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);
--good-ink:#3fc43f;--warn-ink:#fab219;--crit-ink:#f07070;--doing:#3987e5;--doing-ink:#7fb2f0;
--todo:#4a4a46;--crit-wash:#2e1717;--warn-wash:#2b2312;--ring:rgba(255,255,255,.18)}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
font:15px/1.6 system-ui,-apple-system,"Segoe UI","Noto Sans CJK JP","Hiragino Sans",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:24px;margin:0 0 4px;font-weight:650}
h2{font-size:17px;margin:0 0 10px;font-weight:650}
h3{font-size:15px;margin:0 0 6px;font-weight:650}
p{margin:0 0 8px;text-wrap:pretty}
::selection{background:var(--doing);color:#fff}
:focus-visible{outline:2px solid var(--doing);outline-offset:2px;border-radius:2px}
.meta{color:var(--ink-2);font-size:13px;display:flex;flex-wrap:wrap;gap:4px 18px;margin-top:6px}
.goal{font-size:16px;margin:8px 0 0}
.goal b{font-weight:650}
section{background:var(--surface);border:1px solid var(--ring);border-radius:8px;padding:16px 18px;margin-top:16px}
.lede{color:var(--ink-2);font-size:13px;margin:-4px 0 10px}
.now{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:16px}
.now section{margin-top:0}
.now section.alert{border-color:var(--crit);background:var(--crit-wash)}
ul.items{list-style:none;margin:0;padding:0}
ul.items li{padding:6px 0;border-top:1px solid var(--line)}
ul.items li:first-child{border-top:0;padding-top:0}
.id{font:13px/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink-2);margin-right:6px}
.sub{display:block;color:var(--ink-2);font-size:13px}
.empty{color:var(--muted)}
.ic{flex:none}
.badge{display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;white-space:nowrap;
padding:1px 8px;border-radius:999px;border:1px solid currentColor}
.st-done{color:var(--good-ink)}.st-unverified{color:var(--warn-ink)}.st-blocked{color:var(--crit-ink)}
.st-doing{color:var(--doing-ink)}.st-todo,.st-dropped{color:var(--ink-2)}.st-waiting{color:var(--ink)}
.progress-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px;margin:0 0 4px}
.progress-head strong{font-size:20px;font-weight:650;font-variant-numeric:tabular-nums}
.progress-head span{color:var(--ink-2);font-size:14px}
.strip{margin-top:16px;padding:12px 18px;border-radius:8px;border:1px solid var(--ring);background:var(--surface);
display:grid;grid-template-columns:auto 1fr;gap:2px 20px;align-items:baseline}
.strip p{margin:0}
.strip .verdict{display:flex;align-items:center;gap:8px;font-size:17px;font-weight:650}
.strip .verdict .ic{width:16px;height:16px}
.strip .facts{color:var(--ink-2);font-size:13px;font-variant-numeric:tabular-nums}
.strip .strip-next{grid-column:1/-1;font-size:15px}
.st-blocked-strip{border-color:var(--crit);background:var(--crit-wash)}
.st-unverified-strip{border-color:var(--warn);background:var(--warn-wash)}
.bar{display:flex;gap:2px;height:28px;width:100%;margin:6px 0 10px}
.bar span{display:block;height:100%;border-radius:4px;min-width:4px}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;font-size:13px;color:var(--ink-2);margin:0;padding:0;list-style:none}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.f-done{background:var(--good)}.f-unverified{background:var(--warn)}.f-blocked{background:var(--crit)}
.f-doing{background:var(--doing)}.f-todo,.f-open{background:var(--todo)}
.f-waiting{background:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 10px 7px 0;border-top:1px solid var(--line)}
th{font-size:12px;font-weight:600;color:var(--ink-2);border-top:0;white-space:nowrap}
td.num,td.time{font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--ink-2);font-size:13px}
code{font:13px ui-monospace,SFMono-Regular,Menlo,monospace}
.decisions{display:grid;gap:12px}
.decision{border-top:1px solid var(--line);padding-top:10px;margin-top:0}
.decision:first-child{border-top:0;padding-top:0}
.decision>summary{list-style-position:outside;margin-left:1em;color:var(--ink)}
.decision>summary h3{display:inline;margin:0}
.decision dl{display:grid;grid-template-columns:5.5em 1fr;gap:4px 12px;margin:6px 0 0;font-size:14px}
.decision dt{color:var(--ink-2);font-size:13px}
.decision dd{margin:0;text-wrap:pretty}
.decision ul{margin:0;padding-left:1.2em}
details{margin-top:10px}
summary{cursor:pointer;color:var(--ink-2);font-size:13px}
.warnrow td{background:var(--warn-wash)}
.critrow td{background:var(--crit-wash)}
footer{color:var(--muted);font-size:12px;margin-top:24px}
@media (max-width:640px){.decision dl{grid-template-columns:1fr}.strip{grid-template-columns:1fr}}
@media (forced-colors:active){.bar span{border:1px solid CanvasText}}
"""


def e(value):
    return html.escape(redact("" if value is None else str(value)), quote=True)


def fmt_time(value):
    try:
        t = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return "-"
    return t.strftime("%Y-%m-%d %H:%M")


def badge(status):
    label, ic, cls = STATUS.get(status, (status, "circle", "st-todo"))
    return f'<span class="badge {cls}">{icon(ic)}{e(label)}</span>'


def short(sha):
    return e((sha or "")[:8]) or "-"


def items_list(rows, empty):
    if not rows:
        return f'<p class="empty">{e(empty)}</p>'
    return '<ul class="items">' + "".join(f"<li>{r}</li>" for r in rows) + "</ul>"


def test_state(t, current_head):
    """Return (label, css class, row class). A pass on an older commit needs a rerun."""
    r = t.get("result")
    if r == "fail":
        return "失敗", "st-blocked", "critrow"
    if r == "skip":
        return "未実施", "st-todo", ""
    if current_head and t.get("git_head") and t["git_head"] != current_head:
        return "要再実行", "st-unverified", "warnrow"
    if t.get("git_dirty"):
        return "成功（未コミット）", "st-done", ""
    return "成功", "st-done", ""


def assess(st, current_head):
    """Shared by the per-project strip and the all-projects index so both say the same thing."""
    blockers = sum(1 for b in st.get("blockers", []) if not b.get("resolved_at"))
    unverified = sum(1 for t in st.get("tasks", []) if t.get("status") == "unverified")
    tests = st.get("tests", [])
    failing = sum(1 for t in tests if t.get("result") == "fail")
    rerun = sum(1 for t in tests if test_state(t, current_head)[0] == "要再実行")
    nxt = next((n for n in st.get("next_actions", []) if not n.get("done_at")), None)
    if blockers or failing:
        verdict, cls, ic = "対応が必要な問題があります", "st-blocked", "stop"
    elif unverified or rerun:
        verdict, cls, ic = "止まってはいませんが、確認待ちがあります", "st-unverified", "alert"
    else:
        verdict, cls, ic = "止まっている作業も確認待ちもありません", "st-done", "check"
    facts = [f"ブロッカー {blockers}件", f"失敗中のテスト {failing}件", f"未検証タスク {unverified}件",
             f"要再実行のテスト {rerun}件"]
    waiting = sum(1 for t in st.get("tasks", []) if t.get("status") == "waiting")
    if (st.get("sources") or {}).get("tasks"):
        # Backlog states are not ours to judge; only test results are.
        if failing:
            verdict, cls, ic = "失敗中のテストがあります", "st-blocked", "stop"
        elif rerun:
            verdict, cls, ic = "再実行が必要なテストがあります", "st-unverified", "alert"
        else:
            verdict, cls, ic = "失敗中のテストはありません（残件の状態は正本を参照）", "st-done", "check"
        facts = [f"未完の残件 {sum(1 for t in st['tasks'] if t.get('status') == 'open')}件",
                 f"外部待ち {waiting}件", f"失敗中のテスト {failing}件", f"要再実行のテスト {rerun}件"]
    return verdict, cls, ic, facts, nxt


def next_html(st, nxt, cls_prefix=""):
    src = (st.get("sources") or {}).get("tasks")
    if nxt:
        return f'<p class="{cls_prefix}"><b>次</b> <span class="id">{e(nxt["id"])}</span>{e(nxt["text"])}</p>'
    if src:
        return f'<p class="{cls_prefix}"><b>次</b> {e(src)} の「残件の整理」の順番に従う</p>'
    return f'<p class="{cls_prefix} empty">次のアクションが記録されていません。</p>'


def status_strip(st, current_head):
    verdict, cls, ic, facts, nxt = assess(st, current_head)
    nxt_html = next_html(st, nxt, "strip-next")
    return (f'<div class="strip {cls}-strip" role="status"><p class="verdict {cls}">{icon(ic)}{e(verdict)}</p>'
            f'<p class="facts">{" · ".join(e(f) for f in facts)}</p>{nxt_html}</div>')


def section_now_sourced(st):
    src = st["sources"]["tasks"]
    waiting = [t for t in st["tasks"] if t.get("status") == "waiting"]
    open_ = [t for t in st["tasks"] if t.get("status") == "open"]
    sections = {}
    for t in open_:
        sections[t.get("section") or "-"] = sections.get(t.get("section") or "-", 0) + 1
    waiting_rows = [f'{badge("waiting")} <span class="id">{e(t["id"])}</span>{e(t["title"])}'
                    + (f'<span class="sub">{e(t["note"])}</span>' if t.get("note") else "") for t in waiting]
    section_rows = [f'{e(name)}<span class="sub">未完 {n}件</span>' for name, n in sections.items()]
    return (
        '<div class="now">'
        f'<section aria-labelledby="h-next"><h2 id="h-next">次にやること</h2>'
        f'<p>順番は <code>{e(src)}</code> の「残件の整理」に日付と判断者つきで書かれています。'
        'ダッシュボードは順番を推測しません。</p></section>'
        f'<section aria-labelledby="h-wait"><h2 id="h-wait">外部・出社待ち</h2>'
        f'{items_list(waiting_rows, "待ちの残件はありません。")}</section>'
        f'<section aria-labelledby="h-open"><h2 id="h-open">未完の残件（節ごと）</h2>'
        f'{items_list(section_rows, "未完の残件はありません。")}</section>'
        "</div>")


def section_now(st):
    if (st.get("sources") or {}).get("tasks"):
        return section_now_sourced(st)
    nxt = [n for n in st.get("next_actions", []) if not n.get("done_at")]
    blockers = [b for b in st.get("blockers", []) if not b.get("resolved_at")]
    active = [t for t in st.get("tasks", []) if t.get("status") in ("doing", "unverified")]
    active.sort(key=lambda t: (t.get("status") != "doing", t.get("updated_at", "")))

    next_rows = [f'<span class="id">{e(n["id"])}</span>{e(n["text"])}' for n in nxt]
    blocker_rows = [
        f'<span class="id">{e(b["id"])}</span>{e(b["text"])}'
        f'<span class="sub">{"タスク " + e(b["task"]) + " を止めている · " if b.get("task") else ""}'
        f'{fmt_time(b.get("created_at"))} から</span>'
        for b in blockers]
    active_rows = [
        f'{badge(t["status"])} <span class="id">{e(t["id"])}</span>{e(t["title"])}'
        + (f'<span class="sub">{e(t["note"])}</span>' if t.get("note") else "")
        for t in active]
    alert = ' class="alert"' if blockers else ""
    return (
        '<div class="now">'
        f'<section aria-labelledby="h-next"><h2 id="h-next">次にやること</h2>'
        f'{items_list(next_rows, "記録された次のアクションはありません。")}</section>'
        f'<section{alert} aria-labelledby="h-block"><h2 id="h-block">未解決のブロッカー</h2>'
        f'{items_list(blocker_rows, "作業を止めている問題はありません。")}</section>'
        f'<section aria-labelledby="h-doing"><h2 id="h-doing">いま手を付けている作業</h2>'
        f'{items_list(active_rows, "進行中・未検証のタスクはありません。")}</section>'
        "</div>")


def section_progress(st):
    tasks = [t for t in st.get("tasks", []) if t.get("status") not in HIDDEN]
    total = len(tasks)
    counts = {s: sum(1 for t in tasks if t.get("status") == s) for s in BAR_ORDER}
    if total == 0:
        return ('<section aria-labelledby="h-prog"><h2 id="h-prog">全体の進捗</h2>'
                '<p class="empty">タスクがまだ登録されていません。</p></section>')
    pct = round(100 * counts["done"] / total)
    aria = "、".join(f"{STATUS[s][0]} {counts[s]}件" for s in BAR_ORDER if counts[s])
    parts = "".join(
        f'<span class="f-{s}" style="flex:{counts[s]} 1 0" title="{e(STATUS[s][0])} {counts[s]}件"></span>'
        for s in BAR_ORDER if counts[s])
    legend = "".join(
        f'<li><i class="f-{s}" aria-hidden="true"></i>{e(STATUS[s][0])} {counts[s]}</li>'
        for s in BAR_ORDER if counts[s])
    src = (st.get("sources") or {}).get("tasks")
    if src:
        basis = (f'{e(src)} で「済」の印が付いた残件を完了として数えています。'
                 '印の無い残件は、途中まで進んでいても「未完」です。')
    else:
        basis = '完了は確認方法まで記録したタスクだけを数えています。'
        if counts["unverified"]:
            basis += f'未検証の{counts["unverified"]}件は実装済みですが、確認結果がまだありません。'
    return (
        '<section aria-labelledby="h-prog"><h2 id="h-prog">全体の進捗</h2>'
        '<p class="progress-head">'
        f'<strong>完了 {counts["done"]} / {total} 件（{pct}%）</strong>'
        f'<span>{basis}</span></p>'
        f'<div class="bar" role="img" aria-label="タスクの内訳: {e(aria)}">{parts}</div>'
        f'<ul class="legend">{legend}</ul></section>')


def section_tests(st, current_head):
    tests = sorted(st.get("tests", []), key=lambda t: t.get("at", ""), reverse=True)
    body = ""
    for t in tests:
        label, cls, row = test_state(t, current_head)
        cmd = f'<span class="sub"><code>{e(t["command"])}</code></span>' if t.get("command") else ""
        ic = {"st-blocked": "stop", "st-unverified": "alert", "st-todo": "circle"}.get(cls, "check")
        body += (f'<tr class="{row}"><td><span class="badge {cls}">{icon(ic)}{e(label)}</span></td>'
                 f'<td>{e(t.get("name"))}{cmd}</td><td class="time">{fmt_time(t.get("at"))}</td>'
                 f'<td class="num"><code>{short(t.get("git_head"))}</code></td>'
                 f'<td>{e(t.get("detail"))}</td></tr>')
    unverified = [t for t in st.get("tasks", []) if t.get("status") == "unverified"]
    note = ""
    if unverified:
        names = "、".join(f'{e(t["id"])} {e(t["title"])}' for t in unverified)
        note = f'<p>{badge("unverified")} 確認待ちのタスク: {names}</p>'
    table = ('<table><thead><tr><th>結果</th><th>テスト・確認項目</th><th>実行日時</th>'
             f'<th>コミット</th><th>補足</th></tr></thead><tbody>{body}</tbody></table>'
             if tests else '<p class="empty">テスト結果はまだ記録されていません。実行していないテストは成功として扱いません。</p>')
    return ('<section aria-labelledby="h-test"><h2 id="h-test">テストと検証</h2>'
            '<p class="lede">成功を記録したあとにコミットが進んだものは「要再実行」として黄色で示します。'
            '「成功（未コミット）」は、コミット前の変更を含む状態で実行した結果です。</p>'
            f'{note}{table}</section>')


def decision_block(d, open_=False):
    def ul(xs):
        return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>" if xs else '<span class="empty">記録なし</span>'
    refs = ", ".join(f"<code>{e(r)}</code>" for r in d.get("refs") or []) or '<span class="empty">記録なし</span>'
    sup = f'（{e(d["superseded_by"])} で置き換え）' if d.get("superseded_by") else ""
    return (f'<details class="decision"{" open" if open_ else ""}><summary><h3><span class="id">{e(d.get("id"))}</span>'
            f'{e(d.get("title"))}{sup}</h3></summary>'
            f'<dl><dt>決めたこと</dt><dd>{e(d.get("decision"))}</dd>'
            # Decisions read from notes carry no separate reason/alternatives; the note has them.
            + ("" if d.get("from_notes") else
               f'<dt>理由</dt><dd>{e(d.get("reason"))}</dd>'
               f'<dt>代替案</dt><dd>{ul(d.get("alternatives"))}</dd>'
               f'<dt>前提</dt><dd>{ul(d.get("assumptions"))}</dd>')
            + f'<dt>{"出典" if d.get("from_notes") else "関連"}</dt><dd>{refs}</dd>'
            f'<dt>日付</dt><dd class="time">{e((d.get("at") or "-")[:10])}</dd></dl></details>'
            if d.get("from_notes") else
            f'<dt>日時</dt><dd class="time">{fmt_time(d.get("at"))}</dd></dl></details>')


def section_decisions(dec):
    items = sorted(dec.get("decisions", []), key=lambda d: d.get("at", ""), reverse=True)
    active = [d for d in items if d.get("status", "active") == "active"]
    old = [d for d in items if d.get("status") == "superseded"]
    body = "".join(decision_block(d, open_=i < 2) for i, d in enumerate(active)) or '<p class="empty">設計判断はまだ記録されていません。</p>'
    if old:
        body += (f'<details><summary>置き換えられた判断（{len(old)}件）</summary>'
                 f'<div class="decisions">{"".join(decision_block(d) for d in old)}</div></details>')
    from_notes = any(d.get("from_notes") for d in items)
    lede = (f'notes の「決めたこと」の表から{len(active)}件を新しい順に読み取っています。理由と経緯は出典の notes にあります。'
            if from_notes else
            f'新しい順に{len(active)}件。最新の2件だけ開いています。前提が崩れた判断は見直してください。')
    return ('<section aria-labelledby="h-dec"><h2 id="h-dec">設計判断とその理由</h2>'
            f'<p class="lede">{lede}</p>'
            f'<div class="decisions">{body}</div></section>')


def section_tasks(st):
    tasks = st.get("tasks", [])
    rank = {s: i for i, s in enumerate(TABLE_ORDER)}
    # Stable sort keeps the backlog's own order within each state.
    shown = sorted((t for t in tasks if t.get("status") not in HIDDEN),
                   key=lambda t: (rank.get(t.get("status"), 99), t.get("updated_at", "")))
    dropped = [t for t in tasks if t.get("status") in HIDDEN]
    src = (st.get("sources") or {}).get("tasks")

    def row(t):
        extra = t.get("evidence") if t.get("status") == "done" else t.get("note")
        prefix = "確認方法: " if t.get("status") == "done" and extra else ""
        last = (f'<td>{e(t.get("section"))}</td>' if src else
                f'<td class="time">{fmt_time(t.get("updated_at"))}</td>')
        return (f'<tr><td>{badge(t.get("status"))}</td><td><span class="id">{e(t.get("id"))}</span>{e(t.get("title"))}</td>'
                f'<td>{e(prefix)}{e(extra)}</td>{last}</tr>')
    head = ('<thead><tr><th>状態</th><th>タスク</th><th>確認方法・メモ</th>'
            f'<th>{"節" if src else "更新"}</th></tr></thead>')
    body = (f'<table>{head}<tbody>{"".join(row(t) for t in shown)}</tbody></table>'
            if shown else '<p class="empty">タスクはまだありません。</p>')
    if dropped:
        body += (f'<details><summary>中止・閉じたタスク（{len(dropped)}件）</summary>'
                 f'<table>{head}<tbody>{"".join(row(t) for t in dropped)}</tbody></table></details>')
    lede = (f'{e(src)} の残件表を読み取って表示しています。状態は規約の印（~~…~~ と「済」「やらない」）'
            'から判定し、印の無いものは「未完」として本文を出しています。B 節の残件は「外部待ち」です。'
            '状態を変えるときは正本を編集してください。'
            if src else '「完了」は確認方法を記録したものだけです。実装しただけのものは「未検証」に入ります。')
    return ('<section aria-labelledby="h-task"><h2 id="h-task">タスク一覧</h2>'
            f'<p class="lede">{lede}</p>{body}</section>')


def section_sessions(st):
    sessions = sorted(st.get("sessions", []), key=lambda s: s.get("started_at") or "", reverse=True)[:10]
    if not sessions:
        return ""
    rows = ""
    for s in sessions:
        if s.get("ended_at"):
            end = f'{fmt_time(s["ended_at"])}<span class="sub">{e(END_REASON.get(s.get("end_reason"), s.get("end_reason")))}</span>'
        else:
            end = f'実行中<span class="sub">最終応答 {fmt_time(s.get("last_seen_at"))}</span>'
        commits = s.get("commits") or []
        commit_html = (f'{len(commits)}件<span class="sub">' + "<br>".join(f"<code>{e(c)}</code>" for c in commits[:5])
                       + ("<br>…" if len(commits) > 5 else "") + "</span>") if commits else "なし"
        rows += (f'<tr><td class="time">{fmt_time(s.get("started_at"))}<span class="sub"><code>{e((s.get("id") or "")[:8])}</code></span></td>'
                 f'<td class="time">{end}</td><td>{commit_html}</td>'
                 f'<td>{e(s.get("summary")) or "<span class=empty>概要なし</span>"}</td></tr>')
    return ('<section aria-labelledby="h-sess"><h2 id="h-sess">直近のセッション</h2>'
            '<table><thead><tr><th>開始</th><th>終了</th><th>そのセッションのコミット</th><th>概要</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></section>')


def section_events(st):
    events = list(reversed(st.get("events", [])))[:20]
    if not events:
        return ""
    rows = "".join(
        f'<tr><td class="time">{fmt_time(v.get("at"))}</td><td>{e(EVENT_KIND.get(v.get("kind"), v.get("kind")))}</td>'
        f'<td>{e(v.get("text"))}</td></tr>' for v in events)
    return ('<section aria-labelledby="h-ev"><h2 id="h-ev">最近の記録</h2>'
            '<details open><summary>新しい順に20件</summary><table><thead><tr><th>日時</th><th>種類</th><th>内容</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></details></section>')


def header(st):
    g = st.get("git") or {}
    if g.get("available"):
        dirty = g.get("dirty_files", 0)
        git_meta = (f'<span>ブランチ <code>{e(g.get("branch"))}</code></span>'
                    f'<span>HEAD <code>{short(g.get("head"))}</code> {e(g.get("head_subject"))}</span>'
                    f'<span>{"未コミットの変更 " + str(dirty) + "件" if dirty else "未コミットの変更なし"}</span>')
    else:
        git_meta = "<span>Git管理外</span>"
    goal = f'<p class="goal"><b>目標</b> {e(st.get("goal"))}</p>' if st.get("goal") else \
        '<p class="goal empty">目標が設定されていません。</p>'
    return (f'<header><h1>{e(st.get("project"))} の開発状況</h1>{goal}'
            f'<div class="meta"><span>データ最終更新 {fmt_time(st.get("updated_at"))}</span>'
            f'<span>Gitの確認 {fmt_time(g.get("checked_at"))}</span>{git_meta}</div></header>')


FAVICON_COLOR = {"st-done": "#0ca30c", "st-unverified": "#fab219", "st-blocked": "#d03b3b"}


def favicon(cls):
    """A signal reaching a node, colored by verdict so a row of tabs reads as status."""
    c = FAVICON_COLOR.get(cls, "#898781")
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
           "<rect x='.5' y='.5' width='31' height='31' rx='7.5' fill='#121211' stroke='#3a3a37'/>"
           f"<path d='M4 17.5h4.5l3-9 5 15 3-6h2.5' fill='none' stroke='{c}' stroke-width='3.2' "
           "stroke-linecap='round' stroke-linejoin='round'/>"
           f"<circle cx='25.5' cy='17.5' r='3.3' fill='{c}'/></svg>")
    # data: keeps it inside the page CSP (img-src data:); only '#' needs escaping here.
    return f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{svg.replace("#", "%23")}">'


def page(title, body, cls="st-done", refresh=None):
    meta_refresh = f'<meta http-equiv="refresh" content="{int(refresh)}">' if refresh else ""
    return (
        "<!doctype html>\n<html lang=\"ja\"><head><meta charset=\"utf-8\">" + meta_refresh +
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; img-src data:\">"
        f"<title>{e(title)}</title>{favicon(cls)}<style>{CSS}{INDEX_CSS}{HELP_CSS}</style></head><body><main>{body}</main></body></html>\n")


INDEX_CSS = """
.projects{display:grid;gap:12px;margin-top:16px}
.project{display:grid;grid-template-columns:minmax(220px,1fr) 2fr;gap:4px 24px;margin-top:0}
.project h2{margin:0}
.project h2 a{color:var(--ink);text-decoration:none}
.project h2 a:hover{text-decoration:underline}
.project .verdict{display:flex;align-items:center;gap:6px;font-weight:650;margin:0}
.project .facts{color:var(--ink-2);font-size:13px;margin:0;font-variant-numeric:tabular-nums}
.project .where{color:var(--muted);font-size:12px;margin:2px 0 0;overflow-wrap:anywhere}
.project.st-blocked-card{border-color:var(--crit)}
.project.st-unverified-card{border-color:var(--warn)}
.back{font-size:13px;margin:0 0 8px}
.back a,.project a{color:var(--doing-ink)}
.waiting{margin-top:16px}
.waiting.has-blocked{border-color:var(--crit);background:var(--crit-wash)}
.waiting table td{vertical-align:baseline}
.waiting .ago{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--ink-2);font-size:13px}
.waiting .others{color:var(--ink-2);font-size:13px;margin:8px 0 0}
@media (max-width:760px){.project{grid-template-columns:1fr}}
"""

AGENT_STATE = {
    # state: (label, icon, css class, rank)
    "blocked": ("承認・回答待ち", "stop", "st-blocked", 0),
    "done": ("応答済み・指示待ち", "alert", "st-unverified", 1),
    "idle": ("指示待ち", "circle", "st-todo", 2),
    "working": ("作業中", "play", "st-doing", 3),
}


def ago(seconds):
    s = max(0, int(seconds))
    if s < 60:
        return f"{s}秒前"
    if s < 3600:
        return f"{s // 60}分前"
    if s < 86400:
        return f"{s // 3600}時間{s % 3600 // 60}分前"
    return f"{s // 86400}日前"


def section_waiting(agents, slug_by_root, now):
    """Sessions that need the user, most urgent and longest-waiting first."""
    waiting = [a for a in agents if a.get("state") in ("blocked", "done", "idle")]
    waiting.sort(key=lambda a: (AGENT_STATE[a["state"]][3], a.get("since", now)))
    working = sum(1 for a in agents if a.get("state") == "working")
    rows = ""
    for a in waiting:
        label, ic, cls, _ = AGENT_STATE[a["state"]]
        root = a.get("root") or a.get("cwd") or ""
        name = e(Path(root).name or root)
        slug = slug_by_root.get(root)
        name_html = f'<a href="/p/{e(slug)}/">{name}</a>' if slug else name
        branch = f'<span class="sub"><code>{e(a.get("branch"))}</code></span>' if a.get("branch") else ""
        pane = f'herdr <code>{e(a["herdr_pane"])}</code>' if a.get("herdr_pane") else "herdr 外"
        rows += (f'<tr><td><span class="badge {cls}">{icon(ic)}{e(label)}</span></td>'
                 f'<td>{name_html}{branch}</td><td>{e(a.get("detail"))}</td>'
                 f'<td class="ago">{ago(now - a.get("since", now))}</td>'
                 f'<td class="ago">{pane}<span class="sub"><code>{e(a.get("session_id", "")[:8])}</code></span></td></tr>')
    blocked = any(a.get("state") == "blocked" for a in agents)
    table = ('<table><thead><tr><th>状態</th><th>プロジェクト</th><th>待っている内容</th><th>待ち始め</th>'
             f'<th>場所</th></tr></thead><tbody>{rows}</tbody></table>' if rows
             else '<p class="empty">あなたを待っているセッションはありません。</p>')
    return (f'<section class="waiting{" has-blocked" if blocked else ""}" aria-labelledby="h-wait">'
            '<h2 id="h-wait">あなたの対応待ち</h2>'
            f'{table}<p class="others">作業中 {working}件 · 30秒ごとに自動で再読み込みします。</p></section>')


HELP_CSS = """
.help section h2{margin-bottom:8px}
.help table{margin:6px 0 4px}
.help td:first-child{white-space:nowrap}
.help pre{margin:6px 0;padding:10px 12px;border-radius:6px;background:var(--page);border:1px solid var(--line);
overflow-x:auto;font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
.help p{max-width:72ch}
"""

P = "python3 ~/.claude/skills/progress-dashboard/scripts/progress.py"


def _rows(pairs):
    return "".join(f"<tr><td>{a}</td><td>{e(b)}</td></tr>" for a, b in pairs)


def render_help(host_label, lan_urls=()):
    """Static usage page; what someone opening the dashboard needs, not the implementation."""
    cmd = lambda c: f"<code>{e(c)}</code>"  # noqa: E731
    sections = [
        ("開き方", f"""
{"".join(f"<p>同じ LAN からは <code>{e(u)}</code> を開いてください。</p>" for u in lan_urls) or
   "<p>LAN には公開していません。公開するときは <code>~/.config/progress-dashboard/serve.env</code> に待ち受けるアドレスを書いて、サービスを再起動します。</p>"}
<p>リモートからは、ssh の設定（WSL の <code>~/.ssh/config</code> の該当ホスト）に1行足して接続し、<code>http://localhost:8765/</code> を開きます。</p>
<pre>LocalForward 8765 127.0.0.1:8765</pre>
<p>一覧ページは30秒ごとに自動で再読み込みします。各プロジェクトのページは、F5 で最新になります。</p>"""),
        ("プロジェクトを一覧に足す・外す", f"""
<p>足したいリポジトリで、次のどちらかを一度だけ実行してください。</p>
<table><thead><tr><th>場合</th><th>コマンド</th></tr></thead><tbody>
<tr><td>タスクと判断をダッシュボードで管理する</td><td>{cmd(P + ' init --goal "達成したいこと"')}</td></tr>
<tr><td>残件の正本が既にある（notes/remaining.md など）</td><td>{cmd(P + ' init --tasks-from notes/remaining.md --decisions-from notes --goal "..."')}<br>チームのリポジトリなら {cmd('echo .claude/dashboard/ >> .git/info/exclude')} も実行する</td></tr>
</tbody></table>
<p>一覧から外すときは、そのリポジトリで {cmd(P + ' unregister')} を実行します。<code>.claude/dashboard/</code> が残っていると次に Claude を起動したときに再び登録されるので、使わなくなったらディレクトリごと消してください。</p>
<p>一覧に載せたプロジェクトは、同じ LAN にいる人なら誰でも見られます。公開したくないリポジトリでは init しないでください。</p>"""),
        ("記録のしかた", f"""
<p>記録は Claude が作業の節目に CLI で行います。人が手で実行してもかまいません。正本が別にあるプロジェクトでは、task・blocker・next・decision は拒否されるので、正本のファイルを編集してください。</p>
<table><thead><tr><th>コマンド</th><th>使うとき</th></tr></thead><tbody>{_rows([
    (cmd("task add \"タイトル\""), "新しい作業が決まった"),
    (cmd("task set T3 doing"), "作業に着手した"),
    (cmd("task set T3 unverified --note \"…\""), "実装したが、まだ確かめていない"),
    (cmd("task set T3 done --evidence \"…\""), "確認まで終えた（確認方法が必須）"),
    (cmd("task set T3 blocked --note \"…\""), "作業を止める問題が見つかった"),
    (cmd("test \"名前\" pass|fail|skip"), "テストや動作確認を実行した"),
    (cmd("decision add --title … --decision … --reason …"), "後から理由を問われそうな判断をした"),
    (cmd("next add \"…\""), "次にやることが決まった"),
    (cmd("note --pivot \"…\""), "作業方針を変えた"),
    (cmd("show"), "短い要約を表示する（Claude の起動時にも自動で表示される）"),
])}</tbody></table>
<p>コマンドの頭には {cmd(P)} が付きます。</p>"""),
        ("表示の読み方", f"""
<table><thead><tr><th>表示</th><th>意味</th></tr></thead><tbody>{_rows([
    (badge("done"), "確認方法まで記録した完了。正本を読むプロジェクトでは「済」の印がある残件"),
    (badge("unverified"), "実装したが、確認結果がまだ記録されていない"),
    (badge("doing"), "着手している"),
    (badge("blocked"), "作業を止める問題がある"),
    (badge("waiting"), "出社やベンダの回答を待っている（正本の B 節）"),
    (badge("open"), "正本に状態の印が無い残件。途中まで進んでいても未完として本文を出す"),
    ("<span class='badge st-unverified'>要再実行</span>", "成功を記録したあとにコミットが進んだテスト"),
])}</tbody></table>
<p>「あなたの対応待ち」には、このマシンで動いている Claude Code のセッションが出ます（herdr の外で起動したものも含みます）。</p>
<table><thead><tr><th>状態</th><th>意味</th></tr></thead><tbody>{_rows([
    ("承認・回答待ち", "ツールの承認か、質問への回答を待っている。これがあるとファビコンが赤になる"),
    ("応答済み・指示待ち", "応答を終え、結果の確認か次の指示を待っている"),
    ("指示待ち", "起動直後か、応答のあと60秒以上入力がない"),
])}</tbody></table>
<p>プロンプトの本文やコマンドの中身は保存せず、表示もしません。</p>"""),
        ("サーバーの操作", f"""
<p>このページは systemd のユーザーサービス <code>progress-dashboard</code> が配信しています。</p>
<pre>systemctl --user status progress-dashboard     # 状態
systemctl --user restart progress-dashboard    # render.py などを直したあと
journalctl --user -u progress-dashboard -e     # ログ</pre>
<p>データ（status.json、正本の Markdown、セッションの状態）はリクエストのたびに読むので、変えても再起動は要りません。Hook の失敗は各プロジェクトの <code>.claude/dashboard/hook.log</code> に残ります。詳しい仕様は <code>~/.claude/skills/progress-dashboard/SKILL.md</code> にあります。</p>"""),
    ]
    body = "".join(f'<section aria-labelledby="h-{i}"><h2 id="h-{i}">{e(t)}</h2>{c}</section>'
                   for i, (t, c) in enumerate(sections))
    return page("使い方 · 開発状況ダッシュボード",
                f'<p class="back"><a href="/">← 全プロジェクト</a></p>'
                f'<header><h1>使い方</h1><div class="meta"><span>{e(host_label)}</span></div></header>'
                f'<div class="help">{body}</div>')


def render_index(projects, host_label, agents=(), now=None):
    """projects: list of dicts with slug, root, and either status/decisions or error."""
    import time as _time
    now = now if now is not None else _time.time()
    rank = {"st-blocked": 0, "st-unverified": 1, "st-done": 2}
    cards = []
    for p in projects:
        if p.get("error"):
            cards.append((3, "", f'<section class="project"><div><h2>{e(Path(p["root"]).name)}</h2>'
                             f'<p class="where">{e(p["root"])}</p></div>'
                             f'<p class="empty">読み込めません: {e(p["error"])}</p></section>'))
            continue
        st = p["status"]
        verdict, cls, ic, facts, nxt = assess(st, (st.get("git") or {}).get("head"))
        tasks = [t for t in st.get("tasks", []) if t.get("status") not in HIDDEN]
        done = sum(1 for t in tasks if t.get("status") == "done")
        nxt_html = next_html(st, nxt)
        goal = f'<p>{e(st.get("goal"))}</p>' if st.get("goal") else ""
        cards.append((rank.get(cls, 3), st.get("updated_at", ""),
            f'<section class="project {cls}-card"><div>'
            f'<h2><a href="/p/{e(p["slug"])}/">{e(st.get("project"))}</a></h2>'
            f'<p class="where">{e(p["root"])}</p>'
            f'<p class="facts">完了 {done} / {len(tasks)} 件 · 最終更新 {fmt_time(st.get("updated_at"))}</p></div>'
            f'<div><p class="verdict {cls}">{icon(ic)}{e(verdict)}</p>'
            f'<p class="facts">{" · ".join(e(f) for f in facts)}</p>{goal}{nxt_html}</div></section>'))
    # Problems first, then most recently updated.
    cards.sort(key=lambda c: c[1], reverse=True)
    cards.sort(key=lambda c: c[0])
    body = "".join(c[2] for c in cards) or '<p class="empty">登録されたプロジェクトはありません。各リポジトリで progress.py init を実行してください。</p>'
    generated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    worst = min((c[0] for c in cards), default=2)
    if any(a.get("state") == "blocked" for a in agents):
        worst = 0
    worst_cls = {0: "st-blocked", 1: "st-unverified"}.get(worst, "st-done")
    slug_by_root = {p["root"]: p["slug"] for p in projects}
    return page("全プロジェクトの開発状況",
                f'<header><h1>全プロジェクトの開発状況</h1>'
                f'<div class="meta"><span>{len(projects)}件</span><span>表示 {generated}</span>'
                f'<span>{e(host_label)}</span><span><a href="/help">使い方</a></span></div></header>'
                + section_waiting(agents, slug_by_root, now)
                + f'<div class="projects">{body}</div>'
                '<footer>対応が必要なものから順に並べています。各プロジェクトの詳細はプロジェクト名から開けます。</footer>',
                worst_cls, refresh=30)


def render_html(st, dec, current_head=None):
    generated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    return (
        "<!doctype html>\n<html lang=\"ja\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; img-src data:\">"
        f"<title>{e(st.get('project'))} 開発状況</title>{favicon(assess(st, current_head)[1])}"
        f"<style>{CSS}</style></head><body><main>"
        + header(st)
        + status_strip(st, current_head)
        + section_now(st)
        + section_progress(st)
        + section_tests(st, current_head)
        + section_decisions(dec)
        + section_tasks(st)
        + section_sessions(st)
        + section_events(st)
        + f'<footer>生成 {generated} · 元データ .claude/dashboard/status.json, decisions.json · '
          '更新はprogress-dashboard skillのprogress.pyで行います。</footer>'
        + "</main></body></html>\n")
