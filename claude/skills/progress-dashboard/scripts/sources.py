"""Read a project's existing source of truth instead of owning tasks and decisions.

For repos that already keep a backlog in Markdown (e.g. notes/remaining.md) the
dashboard only displays it. State is taken from explicit markers only; anything
without a marker stays "open" with its text shown, so nothing is marked done by guess.
"""

import re
from pathlib import Path

ID_RE = re.compile(r"^[A-Z]\d{1,3}$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
STRUCK_RE = re.compile(r"^\s*(\*\*)?~~")
# "済 (10-08 …", "**済 (…", "**10-09 済 (…": a cell that opens with a done marker.
DONE_CELL_RE = re.compile(r"^\s*(\*\*)?\s*(\d{1,2}-\d{1,2}\s*)?済")
DONE_WORD_RE = re.compile(r"済|Close")
DROP_WORD_RE = re.compile(r"やらない|追わない")
WAITING_SECTION_RE = re.compile(r"^B[.．]")
DECISION_HEADING_RE = re.compile(r"^決めたこと")
MAX_NOTE = 200
NOTE_COLUMNS = ("扱い", "中身", "待ち")


def clean(text):
    text = text.replace("~~", "").replace("**", "").replace("★", "")
    return re.sub(r"\s+", " ", text).strip()


def cells(line):
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def is_separator(row):
    return all(re.fullmatch(r":?-{3,}:?", c) for c in row if c)


def classify(row, section):
    title_struck = bool(STRUCK_RE.match(row[1])) or bool(STRUCK_RE.match(row[0]))
    rest = " ".join(row[1:])
    if title_struck and DONE_WORD_RE.search(rest):
        return "done"
    if any(DONE_CELL_RE.match(c) for c in row[2:]):
        return "done"
    if title_struck and DROP_WORD_RE.search(rest):
        return "dropped"
    if title_struck:
        return "closed"
    if WAITING_SECTION_RE.match(section):
        return "waiting"
    return "open"


def short(text):
    text = clean(text)
    return text[:MAX_NOTE] + ("…" if len(text) > MAX_NOTE else "")


def read_backlog(path):
    """Rows of every table whose first column is a backlog ID (A1, P3, B2 …)."""
    tasks, section, header = [], "", []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            section = clean(m.group(2))
            continue
        if not line.lstrip().startswith("|"):
            continue
        row = cells(line)
        if len(row) < 2 or is_separator(row):
            continue
        rid = clean(row[0])
        if not ID_RE.match(rid):
            header = [clean(c) for c in row]
            continue
        status = classify(row, section)
        evidence = ""
        if status == "done":
            evidence = next((short(c) for c in row[2:] if DONE_CELL_RE.match(c)), "")
            if not evidence:
                # "~~title~~ **10-13 済** (…)": the result follows the struck title.
                cell = next((c for c in row[1:] if DONE_WORD_RE.search(c.rsplit("~~", 1)[-1])), row[1])
                evidence = short(cell.rsplit("~~", 1)[-1])
        col = next((header.index(n) for n in NOTE_COLUMNS if n in header), len(row) - 1)
        note = short(row[col]) if 2 <= col < len(row) else ""
        tasks.append({
            "id": rid, "title": clean(row[1])[:160], "status": status,
            "note": "" if status == "done" else note, "evidence": evidence,
            "section": section, "updated_at": "",
        })
    return tasks


def read_decisions(notes_dir, root):
    """Rows of `| # | 項目 | 決定 |` tables under 決めたこと headings, newest file first."""
    out = []
    files = sorted(Path(notes_dir).rglob("*.md"), key=lambda p: p.name, reverse=True)
    for f in files:
        heading, in_decision = "", False
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = HEADING_RE.match(line)
            if m:
                heading = clean(m.group(2))
                in_decision = bool(DECISION_HEADING_RE.match(heading))
                continue
            if not in_decision or not line.lstrip().startswith("|"):
                continue
            row = cells(line)
            if len(row) < 3 or is_separator(row) or clean(row[0]) in ("#", ""):
                continue
            rel = f.relative_to(root)
            date = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
            out.append({
                "id": f"{f.stem[:10]}#{clean(row[0])}",
                "at": (date.group(1) + "T00:00:00") if date else "",
                "title": clean(row[1])[:160], "decision": clean(row[2])[:400],
                "reason": "", "alternatives": [], "assumptions": [],
                "refs": [f"{rel}「{heading}」"], "status": "active", "from_notes": True,
            })
    return out


def source_mtime(root, sources):
    """Newest mtime among the source files, so hooks re-render when they change."""
    newest = 0.0
    tasks = sources.get("tasks")
    if tasks:
        p = Path(root) / tasks
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
    notes = sources.get("decisions")
    if notes:
        for f in (Path(root) / notes).rglob("*.md"):
            newest = max(newest, f.stat().st_mtime)
    return newest
