#!/usr/bin/env bash

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGMSG_DIR="$HOME/.agents/skills/agmsg"

for command in git sqlite3; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "error: $command is required" >&2
    exit 1
  fi
done

"$DOTFILES_DIR/scripts/setup-skills.sh"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

git clone --depth 1 https://github.com/fujibee/agmsg.git "$tmp_dir/agmsg"

if [[ -f "$AGMSG_DIR/.agmsg" ]]; then
  "$tmp_dir/agmsg/install.sh" --cmd agmsg --update
else
  "$tmp_dir/agmsg/install.sh" --cmd agmsg
fi
