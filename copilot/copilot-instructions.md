# Copilot CLI Instructions

## Notifications

When starting a long-running operation (build, test, install, etc.) that requires the user to wait:
1. Tell the user to wait (e.g. "⏳ ビルド中です、お待ちください...")
2. After the operation completes, send a tmux bell notification by running: `printf '\a'`

This allows the user to see a notification in the tmux status bar when the task is done.
