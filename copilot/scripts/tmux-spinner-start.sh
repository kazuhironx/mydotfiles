#!/usr/bin/env bash
set -euo pipefail

[[ -z "${TMUX:-}" ]] && exit 0

PANE_ID="${TMUX_PANE:-$(tmux display-message -p '#{pane_id}' 2>/dev/null || echo 'default')}"
WINDOW_ID=$(tmux display-message -t "${PANE_ID}" -p '#{window_id}' 2>/dev/null || echo '')
[[ -z "$WINDOW_ID" ]] && exit 0

SUFFIX="${PANE_ID//[^a-zA-Z0-9]/_}"
PID_FILE="/tmp/copilot-tmux-spinner-${SUFFIX}.pid"
NAME_FILE="/tmp/copilot-tmux-spinner-${SUFFIX}.name"

tmux set-option -w -t "$WINDOW_ID" -u @unread 2>/dev/null || true

if [[ -f "$PID_FILE" ]]; then
    kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE"
fi

if [[ ! -f "$NAME_FILE" ]]; then
    tmux display-message -t "$WINDOW_ID" -p '#{window_name}' > "$NAME_FILE" 2>/dev/null
fi
ORIGINAL_NAME=$(cat "$NAME_FILE" 2>/dev/null || echo 'copilot')

(
    SPINNER=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    i=0
    while true; do
        tmux rename-window -t "$WINDOW_ID" "${SPINNER[$i]} ${ORIGINAL_NAME}" 2>/dev/null || break
        i=$(( (i + 1) % ${#SPINNER[@]} ))
        sleep 0.1
    done
) > /dev/null 2>&1 &
disown

echo $! > "$PID_FILE"
exit 0
