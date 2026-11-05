#!/usr/bin/env python3
"""Check Issue/PR references in a PR body.

Same repo -> `#N`, other repo -> `owner/repo#N`. GitHub resolves a bare `#N`
against the PR's own repo, so a bare number meant for another repo silently
links to the wrong item. This script flags that and the other forms GitHub
does not shorten for us.

Usage: ref-check.py BODY.md [--repo OWNER/REPO]
Exit status: 1 if any ✗, else 0.
"""

import argparse
import json
import re
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


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_remote(url):
    m = re.search(r"(?:[:/])(?P<o>[\w.-]+)/(?P<r>[\w.-]+?)(?:\.git)?/?$", url.strip())
    return f"{m['o']}/{m['r']}" if m else None


def current_repo():
    # gh may be logged in as an account that cannot see this repo, so the git
    # remote is the source of truth.
    p = run(["git", "remote", "get-url", "origin"])
    if p.returncode == 0:
        repo = parse_remote(p.stdout)
        if repo:
            return repo
    p = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("--repo", help="PR を出すリポジトリ（既定: git remote origin）")
    args = ap.parse_args()

    cur = args.repo or current_repo()
    if not cur:
        print("✗ PR を出すリポジトリが分からない。--repo OWNER/REPO を渡す")
        return 1
    print(f"repo: {cur}")

    text = open(args.body, encoding="utf-8").read()
    errors = 0

    def out(mark, lineno, ref, msg):
        nonlocal errors
        errors += mark == "✗"
        print(f"{mark} L{lineno} {ref}: {msg}")

    for lineno, line in scan_lines(text):
        masked = line
        for m in URL_RE.finditer(line):
            repo = f"{m['o']}/{m['r']}"
            short = f"#{m['n']}" if repo.lower() == cur.lower() else f"{repo}#{m['n']}"
            out("✗", lineno, m.group(), f"URL ではなく {short} と書く")
        masked = URL_RE.sub(lambda m: " " * len(m.group()), masked)

        for m in FULL_RE.finditer(masked):
            repo = f"{m['o']}/{m['r']}"
            if repo.lower() == cur.lower():
                out("△", lineno, m.group(), f"同じリポジトリなので #{m['n']} でよい")
                continue
            st, desc = lookup(repo, m["n"])
            if st == "missing":
                out("✗", lineno, m.group(), f"{repo} に #{m['n']} が無い")
            elif st == "found":
                out("✓", lineno, m.group(), desc)
            else:
                out("?", lineno, m.group(), f"未確認（{desc}）")
        masked = FULL_RE.sub(lambda m: " " * len(m.group()), masked)

        for m in NO_OWNER_RE.finditer(masked):
            out("✗", lineno, m.group(), f"owner が無いと GitHub はリンクしない。<owner>/{m['r']}#{m['n']} と書く")
        masked = NO_OWNER_RE.sub(lambda m: " " * len(m.group()), masked)

        for m in BARE_RE.finditer(masked):
            st, desc = lookup(cur, m["n"])
            if st == "missing":
                out("✗", lineno, m.group(), f"{cur} に無い。別リポジトリなら <owner>/<repo>#{m['n']} と書く")
            elif st == "found":
                out("✓", lineno, m.group(), f"{cur} の {desc} — 意図した相手か確かめる")
            else:
                out("?", lineno, m.group(), f"未確認（{desc}）")

    print(f"✗ {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
