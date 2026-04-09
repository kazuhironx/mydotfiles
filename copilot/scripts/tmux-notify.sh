#!/usr/bin/env bash
set -euo pipefail

[[ -z "${TMUX:-}" ]] && exit 0

PANE_ID="${TMUX_PANE:-$(tmux display-message -p '#{pane_id}' 2>/dev/null || echo '')}"
[[ -z "$PANE_ID" ]] && exit 0

WINDOW_ID=$(tmux display-message -t "${PANE_ID}" -p '#{window_id}' 2>/dev/null || echo '')
[[ -z "$WINDOW_ID" ]] && exit 0

# ● マーカー設定
tmux set-option -w -t "$WINDOW_ID" @unread 1 2>/dev/null || true

# ベル送信
printf '\a' > "$(tmux display-message -t "${PANE_ID}" -p '#{pane_tty}' 2>/dev/null)" 2>/dev/null || true

exit 0
