#!/usr/bin/env bash
set -euo pipefail

[[ -z "${TMUX:-}" ]] && exit 0

PANE_ID="${TMUX_PANE:-$(tmux display-message -p '#{pane_id}' 2>/dev/null || echo 'default')}"
WINDOW_ID=$(tmux display-message -t "${PANE_ID}" -p '#{window_id}' 2>/dev/null || echo '')

SUFFIX="${PANE_ID//[^a-zA-Z0-9]/_}"
PID_FILE="/tmp/copilot-tmux-spinner-${SUFFIX}.pid"
NAME_FILE="/tmp/copilot-tmux-spinner-${SUFFIX}.name"

if [[ -f "$PID_FILE" ]]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE"
fi

if [[ -n "$WINDOW_ID" ]]; then
    if [[ -f "$NAME_FILE" ]]; then
        ORIGINAL_NAME=$(cat "$NAME_FILE" 2>/dev/null)
        tmux rename-window -t "$WINDOW_ID" "$ORIGINAL_NAME" 2>/dev/null || true
        rm -f "$NAME_FILE"
    else
        tmux set-option -w -t "$WINDOW_ID" automatic-rename on 2>/dev/null || true
    fi

    # 常に@unreadフラグを設定
    tmux set-option -w -t "$WINDOW_ID" @unread 1 2>/dev/null || true
    # 常にbellを送る
    printf '\a' > "$(tmux display-message -t "${PANE_ID}" -p '#{pane_tty}' 2>/dev/null)"
fi
exit 0
