#!/usr/bin/env bash
# Claude Code statusLine
# stdin に来る JSON のスキーマは `claude` バイナリの実装に合わせている:
#   model{id,display_name} workspace{current_dir,project_dir} version output_style{name}
#   cost{total_cost_usd,total_lines_added,total_lines_removed}
#   context_window{total_input_tokens,context_window_size,used_percentage}
#   rate_limits{five_hour{used_percentage,resets_at},seven_day{...}}  ← API 応答を1度観測するまで欠落する
#   exceeds_200k_tokens fast_mode effort{level} thinking{enabled} agent{name} worktree{...} pr{...}
set -uo pipefail

input=$(cat)

j() { printf '%s' "$input" | jq -r "$1" 2>/dev/null; }

C()  { printf '\033[38;5;%sm' "$1"; }
R='\033[0m'; B='\033[1m'
DIM=$(C 244); SEP="${DIM}│${R}"

# 使用率に応じた色。閾値は「まだ余裕/そろそろ/危険」の3段。
pct_color() {
  local p=${1%%.*}
  if   [ "$p" -ge 90 ]; then C 203
  elif [ "$p" -ge 75 ]; then C 215
  elif [ "$p" -ge 50 ]; then C 179
  else C 114
  fi
}

bar() { # bar <pct> <width>
  local p=${1%%.*} w=$2 i filled
  [ "$p" -gt 100 ] && p=100
  filled=$(( p * w / 100 ))
  printf '%s' "$(pct_color "$p")"
  for ((i = 0; i < w; i++)); do
    if [ "$i" -lt "$filled" ]; then printf '█'; else printf "${DIM}░$(pct_color "$p")"; fi
  done
  printf '%b' "$R"
}

human_tokens() { # 68123 -> 68k
  local n=$1
  if   [ "$n" -ge 1000000 ]; then printf '%d.%dM' $((n/1000000)) $(( (n%1000000)/100000 ))
  elif [ "$n" -ge 1000 ];    then printf '%dk' $((n/1000))
  else printf '%d' "$n"
  fi
}

until_str() { # epoch秒 -> "2h13m" / "3d4h"
  local target=$1 now diff d h m
  now=$(date +%s)
  diff=$(( target - now ))
  [ "$diff" -lt 0 ] && diff=0
  d=$(( diff / 86400 )); h=$(( (diff % 86400) / 3600 )); m=$(( (diff % 3600) / 60 ))
  if   [ "$d" -gt 0 ]; then printf '%dd%dh' "$d" "$h"
  elif [ "$h" -gt 0 ]; then printf '%dh%dm' "$h" "$m"
  else printf '%dm' "$m"
  fi
}

shorten_path() { # ~ 短縮 + 深いパスは中間を …
  local p=${1/#$HOME/\~} IFS='/' parts n
  read -ra parts <<< "$p"
  n=${#parts[@]}
  if [ "$n" -gt 4 ]; then
    printf '%s/…/%s/%s' "${parts[0]}" "${parts[n-2]}" "${parts[n-1]}"
  else
    printf '%s' "$p"
  fi
}

# ---------- 1行目: モデル / 場所 / git ----------
model=$(j '.model.display_name // "?"')
effort=$(j '.effort.level // empty')
fast=$(j '.fast_mode // false')
# jq の // は false も「無い」扱いにするので明示比較する
thinking=$(j 'if .thinking.enabled == false then "false" else "true" end')
style=$(j '.output_style.name // empty')
agent=$(j '.agent.name // empty')
cwd=$(j '.workspace.current_dir // .cwd // "."')
wt=$(j '.worktree.name // empty')
pr=$(j '.pr.number // empty')

line1="$(C 111)${B}${model}${R}"
[ -n "$effort" ] && [ "$effort" != "null" ] && line1+=" $(C 140)·${effort}${R}"
[ "$fast" = "true" ] && line1+=" $(C 220)⚡${R}"
[ "$thinking" = "false" ] && line1+=" ${DIM}nothink${R}"
[ -n "$agent" ] && [ "$agent" != "null" ] && line1+=" $(C 176)@${agent}${R}"
[ -n "$style" ] && [ "$style" != "default" ] && [ "$style" != "null" ] && line1+=" ${DIM}[${style}]${R}"

line1+=" ${SEP} $(C 80)$(shorten_path "$cwd")${R}"

if branch=$(git -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null); then
  dirty=""
  [ -n "$(git -C "$cwd" status --porcelain -uno 2>/dev/null | head -c1)" ] && dirty="$(C 215)*${R}"
  line1+=" $(C 149)⎇ ${branch}${R}${dirty}"
  ahead_behind=$(git -C "$cwd" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null)
  if [ -n "$ahead_behind" ]; then
    behind=${ahead_behind%%[[:space:]]*}; ahead=${ahead_behind##*[[:space:]]}
    [ "$ahead" != "0" ] && line1+=" ${DIM}↑${ahead}${R}"
    [ "$behind" != "0" ] && line1+=" ${DIM}↓${behind}${R}"
  fi
fi
[ -n "$wt" ] && [ "$wt" != "null" ] && line1+=" ${DIM}wt:${wt}${R}"
[ -n "$pr" ] && [ "$pr" != "null" ] && line1+=" $(C 176)#${pr}${R}"

# ---------- 2行目: コンテキスト / レート制限 / コスト ----------
ctx_pct=$(j '.context_window.used_percentage // 0')
ctx_used=$(j '.context_window.total_input_tokens // 0')
ctx_size=$(j '.context_window.context_window_size // 0')
ctx_int=${ctx_pct%%.*}

line2="${DIM}ctx${R} $(bar "$ctx_int" 10) $(pct_color "$ctx_int")${ctx_int}%${R}"
[ "$ctx_size" -gt 0 ] && line2+=" ${DIM}$(human_tokens "$ctx_used")/$(human_tokens "$ctx_size")${R}"

limit_seg() { # limit_seg <label> <jsonキー>
  local label=$1 key=$2 pct reset out
  pct=$(j ".rate_limits.${key}.used_percentage // empty")
  [ -z "$pct" ] || [ "$pct" = "null" ] && return 1
  pct=${pct%%.*}
  out=" ${SEP} ${DIM}${label}${R} $(bar "$pct" 5) $(pct_color "$pct")${pct}%${R}"
  reset=$(j ".rate_limits.${key}.resets_at // empty")
  if [ -n "$reset" ] && [ "$reset" != "null" ]; then
    out+=" ${DIM}↺$(until_str "${reset%%.*}")${R}"
  fi
  printf '%s' "$out"
}

seg=$(limit_seg 5h five_hour) && line2+="$seg"
seg=$(limit_seg 7d seven_day) && line2+="$seg"
if [ -z "$(j '.rate_limits // empty')" ]; then
  line2+=" ${SEP} ${DIM}usage n/a${R}"
fi

cost=$(j '.cost.total_cost_usd // 0')
added=$(j '.cost.total_lines_added // 0')
removed=$(j '.cost.total_lines_removed // 0')
line2+=" ${SEP} $(C 179)\$$(printf '%.2f' "$cost")${R}"
if [ "$added" != "0" ] || [ "$removed" != "0" ]; then
  line2+=" $(C 114)+${added}${R}${DIM}/${R}$(C 203)-${removed}${R}"
fi
[ "$(j '.exceeds_200k_tokens // false')" = "true" ] && line2+=" ${SEP} $(C 203)>200k${R}"

printf '%b\n%b' "$line1" "$line2"
