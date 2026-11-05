#!/usr/bin/env python3
"""Check Issue/PR references in a PR body.

Same repo -> `#N`, other repo -> `owner/repo#N`. GitHub resolves a bare `#N`
against the PR's own repo, so a bare number meant for another repo silently
links to the wrong item. This script flags that and the other forms GitHub
does not shorten for us.

Usage:
  ref-check.py BODY.md [--repo OWNER/REPO]   exit 1 if any ✗
  ref-check.py --hook                         Claude Code PreToolUse(Bash) hook:
                                              reads the hook JSON on stdin and
                                              blocks (exit 2) gh pr/issue
                                              create|edit|comment with a ✗
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys

URL_RE = re.compile(
    r"https?://(?P<host>[\w.-]+)/(?P<o>[\w.-]+)/(?P<r>[\w.-]+)/(?:pull|issues)/(?P<n>\d+)(?![\w/#])"
)
FULL_RE = re.compile(r"(?<![\w./-])(?P<o>[\w.-]+)/(?P<r>[\w.-]+)#(?P<n>\d+)\b")
NO_OWNER_RE = re.compile(r"(?<![\w./#&-])(?P<r>[A-Za-z][\w.-]*)#(?P<n>\d+)\b")
BARE_RE = re.compile(r"(?<![\w/&#-])#(?P<n>\d+)\b")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
GH_WRITE_RE = re.compile(r"\bgh\s+(?:pr|issue)\s+(?:create|edit|comment)\b")


def run(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def parse_remote(url):
    m = re.search(r"(?:[:/])(?P<o>[\w.-]+)/(?P<r>[\w.-]+?)(?:\.git)?/?$", url.strip())
    return f"{m['o']}/{m['r']}" if m else None


def current_repo(cwd=None):
    # gh may be logged in as an account that cannot see this repo, so the git
    # remote is the source of truth.
    p = run(["git", "remote", "get-url", "origin"], cwd)
    if p.returncode == 0:
        repo = parse_remote(p.stdout)
        if repo:
            return repo
    p = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd)
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else None


_repo_visible = {}


def lookup(repo, n):
    """Return ('found', desc) / ('missing', None) / ('unverified', reason)."""
    if repo not in _repo_visible:
        _repo_visible[repo] = run(["gh", "api", f"repos/{repo}", "-q", ".full_name"]).returncode == 0
    if not _repo_visible[repo]:
        return "unverified", f"gh から {repo} が見えない"
    p = run(["gh", "api", f"repos/{repo}/issues/{n}"])
    if p.returncode == 0:
        d = json.loads(p.stdout)
        kind = "PR" if "pull_request" in d else "Issue"
        return "found", f"{kind} [{d.get('state')}] {d.get('title')}"
    if "404" in p.stderr:
        return "missing", None
    return "unverified", p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "gh api 失敗"


def scan_lines(text):
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield i, INLINE_CODE_RE.sub(lambda m: " " * len(m.group()), line)


def blank(regex, s):
    return regex.sub(lambda m: " " * len(m.group()), s)


def check(text, cur):
    """Return (report lines, number of ✗)."""
    out = []
    errors = 0

    def add(mark, lineno, ref, msg):
        nonlocal errors
        errors += mark == "✗"
        out.append(f"{mark} L{lineno} {ref}: {msg}")

    for lineno, line in scan_lines(text):
        for m in URL_RE.finditer(line):
            repo = f"{m['o']}/{m['r']}"
            short = f"#{m['n']}" if repo.lower() == cur.lower() else f"{repo}#{m['n']}"
            add("✗", lineno, m.group(), f"URL ではなく {short} と書く")
        masked = blank(URL_RE, line)

        for m in FULL_RE.finditer(masked):
            repo = f"{m['o']}/{m['r']}"
            if repo.lower() == cur.lower():
                add("△", lineno, m.group(), f"同じリポジトリなので #{m['n']} でよい")
                continue
            st, desc = lookup(repo, m["n"])
            if st == "missing":
                add("✗", lineno, m.group(), f"{repo} に #{m['n']} が無い")
            elif st == "found":
                add("✓", lineno, m.group(), desc)
            else:
                add("?", lineno, m.group(), f"未確認（{desc}）")
        masked = blank(FULL_RE, masked)

        for m in NO_OWNER_RE.finditer(masked):
            add("✗", lineno, m.group(), f"owner が無いと GitHub はリンクしない。<owner>/{m['r']}#{m['n']} と書く")
        masked = blank(NO_OWNER_RE, masked)

        for m in BARE_RE.finditer(masked):
            st, desc = lookup(cur, m["n"])
            if st == "missing":
                add("✗", lineno, m.group(), f"{cur} に無い。別リポジトリなら <owner>/<repo>#{m['n']} と書く")
            elif st == "found":
                add("✓", lineno, m.group(), f"{cur} の {desc} — 意図した相手か確かめる")
            else:
                add("?", lineno, m.group(), f"未確認（{desc}）")
    return out, errors


def heredoc_text(command):
    # The first line holds the gh arguments (e.g. a PR URL) and must not be
    # checked as body text; a heredoc body starts on the next line.
    if "<<" in command:
        return command.split("\n", 1)[1] if "\n" in command else ""
    return command


def bodies_from_command(command, cwd):
    """Yield (body text, repo flag or None) for each gh pr/issue write in command.

    Falls back to the raw command text when it cannot be tokenized (heredocs,
    unbalanced quotes) or the body comes from stdin, since the heredoc body is
    then inside the command string itself.
    """
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        yield heredoc_text(command), None
        return

    i = 0
    while i < len(toks):
        if not (toks[i] == "gh" and i + 2 < len(toks) and toks[i + 1] in ("pr", "issue")
                and toks[i + 2] in ("create", "edit", "comment")):
            i += 1
            continue
        j = i + 3
        repo = None
        texts = []
        while j < len(toks) and toks[j] not in (";", "&&", "||", "|", "&", "(", ")"):
            t = toks[j]
            val = toks[j + 1] if j + 1 < len(toks) else None
            key, eq, inline = t.partition("=")
            if eq:
                val = inline
            consumed = 1 if eq else 2
            if key in ("-R", "--repo") and val:
                repo = val
                j += consumed
                continue
            if key in ("-b", "--body") and val is not None:
                texts.append(val)
                j += consumed
                continue
            if key in ("-F", "--body-file") and val is not None:
                if val == "-":
                    texts.append(heredoc_text(command))
                else:
                    path = os.path.join(cwd, os.path.expanduser(val))
                    try:
                        texts.append(open(path, encoding="utf-8").read())
                    except OSError:
                        pass
                j += consumed
                continue
            j += 1
        for t in texts:
            yield t, repo
        i = j


def hook_main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""
    if not GH_WRITE_RE.search(command):
        return 0
    cwd = data.get("cwd") or os.getcwd()

    reports = []
    for text, repo in bodies_from_command(command, cwd):
        cur = repo or current_repo(cwd)
        if not cur:
            continue
        lines, errors = check(text, cur)
        if errors:
            reports.append(f"repo: {cur}\n" + "\n".join(l for l in lines if not l.startswith("✓")))
    if not reports:
        return 0
    print("ref-check: Issue/PR の参照の書き方に ✗ があるので止めた。"
          "同じリポジトリは #N、別リポジトリは owner/repo#N と書いて実行し直す。\n"
          + "\n\n".join(reports), file=sys.stderr)
    return 2


def main():
    if "--hook" in sys.argv[1:]:
        return hook_main()
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("--repo", help="PR を出すリポジトリ（既定: git remote origin）")
    args = ap.parse_args()

    cur = args.repo or current_repo()
    if not cur:
        print("✗ PR を出すリポジトリが分からない。--repo OWNER/REPO を渡す")
        return 1
    print(f"repo: {cur}")
    lines, errors = check(open(args.body, encoding="utf-8").read(), cur)
    print("\n".join(lines))
    print(f"✗ {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
