#!/usr/bin/env bash
# Re-fetch vendored agent skills from their upstream and show (or apply) the diff.
#
# Usage:
#   scripts/update-skills.sh [--apply] [name...]
#   scripts/update-skills.sh --list
#     --list     : show every skill in the repo as own / vendored, last change,
#                  and trigger text size (no network)
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

# dest | kind | repo | subpath | root extras | keep local | drop
#   kind   github: clone repo default branch, copy subpath (+ root extras)
#          herdr : `herdr --skill` (update herdr itself first)
#          hunk  : `hunk skill path` (update hunkdiff itself first)
#          manual: no fetchable source; print the note in subpath and skip
#          frozen: upstream deleted the skill; print the note in subpath and skip
#   keep   local-only files kept as-is (ATTRIBUTION.md is always kept)
#   drop   upstream files deliberately not vendored (added to DROP)
SOURCES="
agents/skills/empirical-prompt-tuning|github|mizchi/skills|empirical-prompt-tuning||SKILL-ja.md|README.md
agents/skills/explainer|github|mizchi/explainer|skills/explainer|LICENSE||
agents/skills/explainer-book|github|mizchi/explainer|skills/explainer-book|LICENSE||
agents/skills/first-reader|github|mizchi/explainer|skills/first-reader|||
agents/skills/yomiyasu|github|nanaism/yomiyasu|skills/yomiyasu|||
agents/skills/herdr|herdr|||||
agents/skills/hunk-review|hunk|||||
agents/skills/explain-before-shorten|manual||copy the code block from https://zenn.dev/microsoft/articles/explain-before-shorten by hand|||
claude/skills/crit|github|tomasz-tomczyk/crit|integrations/claude-code/skills/crit|||
claude/skills/crit-cli|github|tomasz-tomczyk/crit|integrations/claude-code/skills/crit-cli|||
claude/skills/impeccable|github|pbakaus/impeccable|.claude/skills/impeccable|LICENSE,NOTICE.md||
codex/skills/crit|github|tomasz-tomczyk/crit|integrations/codex/skills/crit|||
codex/skills/crit-cli|github|tomasz-tomczyk/crit|integrations/codex/skills/crit-cli|||
copilot/skills/crit|github|tomasz-tomczyk/crit|integrations/github-copilot/skills/crit|||
copilot/skills/crit-cli|github|tomasz-tomczyk/crit|integrations/github-copilot/skills/crit-cli|||
copilot/skills/cli-mastery|github|github/awesome-copilot|skills/cli-mastery|||
copilot/skills/context-map|github|github/awesome-copilot|skills/context-map|||
copilot/skills/copilot-instructions-blueprint-generator|github|github/awesome-copilot|skills/copilot-instructions-blueprint-generator|||
copilot/skills/create-readme|github|github/awesome-copilot|skills/create-readme|||
copilot/skills/editorconfig|github|github/awesome-copilot|skills/editorconfig|||
copilot/skills/git-commit|github|github/awesome-copilot|skills/git-commit|||
copilot/skills/github-issues|github|github/awesome-copilot|skills/github-issues|||
copilot/skills/lsp-setup|github|github/awesome-copilot|skills/lsp-setup|||
copilot/skills/suggest-awesome-github-copilot-skills|github|github/awesome-copilot|skills/suggest-awesome-github-copilot-skills|||
copilot/skills/gh-cli|frozen||upstream removed the skill in github/awesome-copilot 352def3 (2026-05-14); nothing to fetch|||
copilot/skills/make-skill-template|frozen||upstream removed the skill in github/awesome-copilot 570297c (2026-05-19); nothing to fetch|||
"

# Upstream files deliberately not vendored (plugin metadata, logos).
DROP=(.codex-plugin assets)

# Characters of description + when_to_use, i.e. what every session loads into
# context for this skill. Used as a cost signal when reviewing the set.
trigger_chars() {
  awk '
    /^---$/ { if (++fm == 2) exit; next }
    fm == 1 && /^(description|when_to_use):/ { on = 1; sub(/^[a-z_]+: *[|>]?-? */, ""); printf "%s", $0; next }
    fm == 1 && on && /^[ \t]/ { printf "%s", $0; next }
    { on = 0 }
  ' "$1" | wc -m
}

list_skills() {
  local dir name scope row kind repo subpath origin updated chars t
  # A tool loads the shared skills plus its own, so total per tool.
  local -A total=([shared]=0 [claude]=0 [codex]=0 [copilot]=0)
  printf '%-40s %-7s %-40s %-10s %6s\n' SKILL SCOPE ORIGIN UPDATED CHARS
  for dir in "$DOTFILES_DIR"/{agents,claude,codex,copilot}/skills/*/; do
    dir="${dir%/}"
    [[ -f "$dir/SKILL.md" ]] || continue
    name="$(basename "$dir")"
    scope="$(basename "$(dirname "$(dirname "$dir")")")"
    [[ "$scope" == agents ]] && scope=shared
    row="$(grep -E "^${dir#"$DOTFILES_DIR"/}\|" <<< "$SOURCES" || true)"
    IFS='|' read -r _ kind repo subpath _ <<< "$row"
    case "$kind" in
      github) origin="vendored: $repo" ;;
      herdr|hunk) origin="vendored: bundled with $kind" ;;
      manual) origin="vendored: manual copy" ;;
      frozen) origin="vendored: frozen (removed upstream)" ;;
      *) grep -qs '^Source:' "$dir/ATTRIBUTION.md" && origin="vendored: not in SOURCES" || origin="own" ;;
    esac
    updated="$(git -C "$DOTFILES_DIR" log -1 --format=%cs -- "$dir" 2>/dev/null)"
    chars="$(trigger_chars "$dir/SKILL.md")"
    total[$scope]=$((total[$scope] + chars))
    printf '%-40s %-7s %-40s %-10s %6d\n' "$name" "$scope" "${origin:0:40}" "${updated:-uncommitted}" "$chars"
  done
  for t in claude codex copilot; do
    printf '%-40s %-7s %-40s %-10s %6d\n' TOTAL "$t" "shared + $t" '' $((total[shared] + total[$t]))
  done
}

apply=0
names=()
for arg in "$@"; do
  case "$arg" in
    --apply) apply=1 ;;
    --list) list_skills; exit 0 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
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


changed=()
while IFS='|' read -r dest kind repo subpath extras keep drop; do
  [[ -z "$dest" ]] && continue
  name="$(basename "$dest")"
  wanted "$name" || continue
  local_dir="$DOTFILES_DIR/$dest"
  # Same name can exist per tool (crit), so stage and report by repo path.
  stage="$work/stage/$dest"
  mkdir -p "$stage"
  sha=""

  case "$kind" in
    github)
      src="$(clone "$repo")"
      sha="$(git -C "$src" rev-parse HEAD)"
      if [[ ! -d "$src/$subpath" ]]; then
        echo "!! $dest: $repo/$subpath not found upstream (moved?)"
        continue
      fi
      cp -a "$src/$subpath/." "$stage/"
      IFS=',' read -ra extra_files <<< "$extras"
      for f in "${extra_files[@]}"; do cp -a "$src/$f" "$stage/"; done
      ;;
    herdr) herdr --skill > "$stage/SKILL.md" ;;
    hunk)  cp -a "$(hunk skill path)" "$stage/SKILL.md" ;;
    manual|frozen)
      echo "-- $dest: $kind: $subpath"
      continue
      ;;
  esac

  IFS=',' read -ra drop_files <<< "$drop"
  for d in "${DROP[@]}" "${drop_files[@]}"; do rm -rf "${stage:?}/$d"; done

  IFS=',' read -ra keep_files <<< "ATTRIBUTION.md${keep:+,$keep}"
  for f in "${keep_files[@]}"; do
    [[ -e "$local_dir/$f" ]] && cp -a "$local_dir/$f" "$stage/"
  done

  if diff -r -q "$local_dir" "$stage" > /dev/null; then
    echo "ok $dest: up to date${sha:+ (${sha:0:12})}"
    continue
  fi

  echo "## $dest: changed${sha:+ (upstream ${sha:0:12})}"
  diff -ru "$local_dir" "$stage" | sed "s#$work/stage/#upstream/#; s#$DOTFILES_DIR/##" || true
  changed+=("$dest")

  if [[ $apply -eq 1 ]]; then
    rsync -a --delete "$stage/" "$local_dir/"
    # Only pinned sources (tree/<sha>/) carry a revision worth bumping.
    if [[ -n "$sha" && -f "$local_dir/ATTRIBUTION.md" ]]; then
      sed -i -E "s#/tree/[0-9a-f]{40}/#/tree/$sha/#" "$local_dir/ATTRIBUTION.md"
    fi
    echo "applied $dest"
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
