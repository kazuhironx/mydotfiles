#!/bin/sh
# Abbreviate a path: ~/dev/github.com/code/hoge -> ~/d/g/c/hoge
# - Replace $HOME with ~
# - Shorten every intermediate component to its first character
#   (preserving leading "." for hidden dirs, e.g. ".git" -> ".g")
# - Keep the last component as-is
p="${1:-$PWD}"
case "$p" in
  "$HOME")  printf '~';        exit 0 ;;
  "$HOME"/*) p="~${p#$HOME}" ;;
esac

printf '%s' "$p" | awk -F/ '{
  n = NF
  for (i = 1; i <= n; i++) {
    s = $i
    if (i == n || s == "" || s == "~") {
      printf "%s", s
    } else if (substr(s, 1, 1) == ".") {
      printf "%s", substr(s, 1, 2)
    } else {
      printf "%s", substr(s, 1, 1)
    }
    if (i < n) printf "/"
  }
}'
