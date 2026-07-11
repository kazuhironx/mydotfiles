#!/usr/bin/env bash
# One-shot setup: link every dotfile this repo manages into $HOME,
# then wire up agent skills.
#
# Idempotent. Re-runnable. Refuses to overwrite real files (only replaces
# existing symlinks).

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { printf '%s\n' "$*"; }

link() {
  local src="$1" dest="$2"
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    log "skip:    $dest is a real file/dir (not a symlink), leaving alone"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  ln -sfn "$src" "$dest"
  log "link:    $dest -> $src"
}

# Shells and tools
link "$DOTFILES_DIR/zsh/.zshrc"               "$HOME/.zshrc"
link "$DOTFILES_DIR/tmux/.tmux.conf"          "$HOME/.tmux.conf"
link "$DOTFILES_DIR/herdr/config.toml"         "$HOME/.config/herdr/config.toml"
link "$DOTFILES_DIR/emacs/init.el"            "$HOME/.emacs.d/init.el"
link "$DOTFILES_DIR/starship/starship.toml"   "$HOME/.config/starship.toml"
link "$DOTFILES_DIR/hunk/config.toml"          "$HOME/.config/hunk/config.toml"
link "$DOTFILES_DIR/git/.gitconfig"           "$HOME/.gitconfig"

# AI agent global instructions (single source = agents/AGENTS.md)
link "$DOTFILES_DIR/agents/AGENTS.md"                       "$HOME/.claude/CLAUDE.md"
link "$DOTFILES_DIR/agents/AGENTS.md"                       "$HOME/.codex/AGENTS.md"
link "$DOTFILES_DIR/copilot/copilot-instructions.md"        "$HOME/.copilot/copilot-instructions.md"
link "$DOTFILES_DIR/copilot/scripts"                        "$HOME/.copilot/scripts"

# Per-skill symlinks (shared + tool-specific) into each tool's skills/
"$DOTFILES_DIR/scripts/setup-skills.sh"

# Per-machine git config (only if missing — never overwrite)
if [[ ! -e "$HOME/.gitconfig.local" ]]; then
  cp "$DOTFILES_DIR/git/.gitconfig.local.example" "$HOME/.gitconfig.local"
  log "wrote:   $HOME/.gitconfig.local (edit user.name / user.email)"
else
  log "exists:  $HOME/.gitconfig.local (left alone)"
fi

log ""
log "bootstrap done. edit ~/.gitconfig.local if it was newly created."
