#!/usr/bin/env bash
# Re-fetch vendored agent skills from their upstream and show (or apply) the diff.
#
# Usage:
#   scripts/update-skills.sh [--apply] [name...]
#     no --apply : fetch into a temp dir and print the diff against the repo
#     --apply    : overwrite the repo copy with the fetched one
#     name...    : limit to these skills (default: all in SOURCES)
#
# Why a staging dir + full diff instead of copying in place:
#   upstream can add/remove files, and some skills carry local edits. Building
#   the exact expected tree first lets "no diff" mean "up to date" and keeps
#   local edits visible before anything is overwritten.
#
# Applying only touches files in this repo. Because ~/.<tool>/skills/<name> are
# symlinks into it, the update is live immediately; setup-skills.sh only needs
# re-running when a skill is added or removed.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# dest | kind | repo | subpath | root extras | keep local | drop | mode
#   kind   github: clone repo default branch, copy subpath (+ root extras)
#          herdr : `herdr --skill` (update herdr itself first)
#          hunk  : `hunk skill path` (update hunkdiff itself first)
#          manual: no fetchable source; print the note in subpath and skip
#   keep   local-only files kept as-is (ATTRIBUTION.md is always kept)
#   drop   upstream files deliberately not vendored (added to DROP)
#   mode   verbatim | keep-frontmatter (local SKILL.md frontmatter, upstream body)
SOURCES="
agents/skills/ask-questions-if-underspecified|manual||upstream removed the skill in trailofbits/skills 3742e65 (2026-08-03); nothing to fetch||||
agents/skills/condition-based-waiting|github|obra/superpowers-skills|skills/testing/condition-based-waiting||||keep-frontmatter
agents/skills/root-cause-tracing|github|obra/superpowers-skills|skills/debugging/root-cause-tracing||||keep-frontmatter
agents/skills/systematic-debugging|github|obra/superpowers-skills|skills/debugging/systematic-debugging|||CREATION-LOG.md,test-academic.md,test-pressure-1.md,test-pressure-2.md,test-pressure-3.md|keep-frontmatter
agents/skills/verification-before-completion|github|obra/superpowers-skills|skills/debugging/verification-before-completion||||keep-frontmatter
agents/skills/when-stuck|github|obra/superpowers-skills|skills/problem-solving/when-stuck||||keep-frontmatter
agents/skills/empirical-prompt-tuning|github|mizchi/skills|empirical-prompt-tuning||SKILL-ja.md|README.md|verbatim
agents/skills/explainer|github|mizchi/explainer|skills/explainer|LICENSE|||verbatim
agents/skills/explainer-book|github|mizchi/explainer|skills/explainer-book|LICENSE|||verbatim
agents/skills/first-reader|github|mizchi/explainer|skills/first-reader||||verbatim
agents/skills/yomiyasu|github|nanaism/yomiyasu|skills/yomiyasu||||verbatim
agents/skills/herdr|herdr||||||verbatim
agents/skills/hunk-review|hunk||||||verbatim
agents/skills/explain-before-shorten|manual||copy the code block from https://zenn.dev/microsoft/articles/explain-before-shorten by hand||||
claude/skills/crit|github|tomasz-tomczyk/crit|integrations/claude-code/skills/crit||||verbatim
claude/skills/crit-cli|github|tomasz-tomczyk/crit|integrations/claude-code/skills/crit-cli||||verbatim
claude/skills/impeccable|github|pbakaus/impeccable|.claude/skills/impeccable|LICENSE,NOTICE.md|||verbatim
"

# Upstream files deliberately not vendored (plugin metadata, logos).
DROP=(.codex-plugin assets)

apply=0
names=()
for arg in "$@"; do
  case "$arg" in
    --apply) apply=1 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) names+=("$arg") ;;
  esac
done

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

wanted() {
  local name="$1" n
  [[ ${#names[@]} -eq 0 ]] && return 0
  for n in "${names[@]}"; do [[ "$n" == "$name" ]] && return 0; done
  return 1
}

# One shallow clone per repo, shared by every skill that comes from it.
clone() {
  local repo="$1" dir="$work/repos/${1//\//__}"
  if [[ ! -d "$dir" ]]; then
    git clone --quiet --depth 1 "https://github.com/$repo" "$dir" >&2
  fi
  echo "$dir"
}

frontmatter() { awk 'NR==1 && /^---$/ {f=1; print; next} f {print} f && /^---$/ {exit}' "$1"; }
body()        { awk 'NR==1 && /^---$/ {f=1; next} f && /^---$/ {f=0; b=1; next} !f {print}' "$1"; }

changed=()
while IFS='|' read -r dest kind repo subpath extras keep drop mode; do
  [[ -z "$dest" ]] && continue
  name="$(basename "$dest")"
  wanted "$name" || continue
  local_dir="$DOTFILES_DIR/$dest"
  stage="$work/stage/$name"
  mkdir -p "$stage"
  sha=""

  case "$kind" in
    github)
      src="$(clone "$repo")"
      sha="$(git -C "$src" rev-parse HEAD)"
      if [[ ! -d "$src/$subpath" ]]; then
        echo "!! $name: $repo/$subpath not found upstream (moved?)"
        continue
      fi
      cp -a "$src/$subpath/." "$stage/"
      IFS=',' read -ra extra_files <<< "$extras"
      for f in "${extra_files[@]}"; do cp -a "$src/$f" "$stage/"; done
      ;;
    herdr) herdr --skill > "$stage/SKILL.md" ;;
    hunk)  cp -a "$(hunk skill path)" "$stage/SKILL.md" ;;
    manual)
      echo "-- $name: manual update: $subpath"
      continue
      ;;
  esac

  IFS=',' read -ra drop_files <<< "$drop"
  for d in "${DROP[@]}" "${drop_files[@]}"; do rm -rf "${stage:?}/$d"; done

  if [[ "$mode" == keep-frontmatter ]]; then
    { frontmatter "$local_dir/SKILL.md"; body "$stage/SKILL.md"; } > "$stage/SKILL.md.new"
    mv "$stage/SKILL.md.new" "$stage/SKILL.md"
  fi

  IFS=',' read -ra keep_files <<< "ATTRIBUTION.md${keep:+,$keep}"
  for f in "${keep_files[@]}"; do
    [[ -e "$local_dir/$f" ]] && cp -a "$local_dir/$f" "$stage/"
  done

  if diff -r -q "$local_dir" "$stage" > /dev/null; then
    echo "ok $name: up to date${sha:+ (${sha:0:12})}"
    continue
  fi

  echo "## $name: changed${sha:+ (upstream ${sha:0:12})}"
  diff -ru "$local_dir" "$stage" | sed "s#$work/stage/#upstream/#; s#$DOTFILES_DIR/##" || true
  changed+=("$name")

  if [[ $apply -eq 1 ]]; then
    rsync -a --delete "$stage/" "$local_dir/"
    # Only pinned sources (tree/<sha>/) carry a revision worth bumping.
    if [[ -n "$sha" && -f "$local_dir/ATTRIBUTION.md" ]]; then
      sed -i -E "s#/tree/[0-9a-f]{40}/#/tree/$sha/#" "$local_dir/ATTRIBUTION.md"
    fi
    echo "applied $name"
  fi
done <<< "$SOURCES"

if [[ ${#changed[@]} -eq 0 ]]; then
  echo "all fetched skills are up to date"
elif [[ $apply -eq 0 ]]; then
  echo "changed: ${changed[*]} (re-run with --apply to update)"
else
  echo "updated: ${changed[*]}"
  echo "check ATTRIBUTION.md for version lines (e.g. 'Version:') that need a manual bump"
fi
