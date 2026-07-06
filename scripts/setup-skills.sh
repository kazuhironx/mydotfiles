#!/usr/bin/env bash
# Wire up agent skills from this dotfiles repo into each AI tool's skills directory.
#
# Why per-skill symlinks instead of a single dir symlink:
#   A dir symlink (~/.claude/skills -> agents/skills) makes the entire skills/
#   directory belong to the shared set, so tool-specific skills cannot live
#   alongside. Per-skill symlinks keep ~/.<tool>/skills/ a real directory where
#   shared (symlinked) and tool-only (symlinked or real) skills coexist.
#
# Layout consumed:
#   DOTFILES/agents/skills/<name>     -> linked into ~/.agents/skills/ and every
#                                        tool's ~/.<tool>/skills/
#   DOTFILES/claude/skills/<name>     -> linked into ~/.claude/skills/ only
#   DOTFILES/codex/skills/<name>      -> linked into ~/.codex/skills/ only
#   DOTFILES/copilot/skills/<name>    -> linked into ~/.copilot/skills/ only
#
# Idempotent: re-running replaces existing symlinks of the same name.
# Safe: refuses to overwrite a destination that is a real (non-symlink) file/dir.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SHARED_SRC="$DOTFILES_DIR/agents/skills"
TOOLS=(agents claude codex copilot)

ensure_real_dir() {
  local dir="$1"
  if [[ -L "$dir" ]]; then
    echo "convert: $dir was a symlink, replacing with real directory"
    rm "$dir"
  fi
  mkdir -p "$dir"
}

link_skill() {
  local src="$1" dest_dir="$2"
  local name dest
  name="$(basename "$src")"
  dest="$dest_dir/$name"
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    echo "skip:    $dest is a real file/dir (not a symlink), leaving alone"
    return
  fi
  ln -sfn "$src" "$dest"
  echo "link:    $dest -> $src"
}

link_dir_contents() {
  local src_dir="$1" dest_dir="$2"
  [[ -d "$src_dir" ]] || return 0
  shopt -s nullglob
  for src in "$src_dir"/*/; do
    src="${src%/}"
    [[ -d "$src" ]] || continue
    link_skill "$src" "$dest_dir"
  done
  shopt -u nullglob
}

for tool in "${TOOLS[@]}"; do
  target="$HOME/.${tool}/skills"
  ensure_real_dir "$target"
  link_dir_contents "$SHARED_SRC"                "$target"
  if [[ "$tool" != "agents" ]]; then
    link_dir_contents "$DOTFILES_DIR/$tool/skills" "$target"
  fi
done

echo "done."
