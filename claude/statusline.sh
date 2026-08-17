#!/usr/bin/env bash
# Claude Code statusline: session cost, context %, 5h/7d quota, model.
# Reads JSON payload on stdin; emits one line.

set -u

payload=$(cat)

read -r cost ctx_pct in_tok out_tok cache_r cache_c h5 h5_reset d7 d7_reset model <<<"$(
  jq -r '
    [
      (.cost.total_cost_usd // 0),
      (.context_window.used_percentage // 0),
      (.context_window.current_usage.input_tokens // 0),
      (.context_window.current_usage.output_tokens // 0),
      (.context_window.current_usage.cache_read_input_tokens // 0),
      (.context_window.current_usage.cache_creation_input_tokens // 0),
      (.rate_limits.five_hour.used_percentage // -1),
      (.rate_limits.five_hour.resets_at // 0),
      (.rate_limits.seven_day.used_percentage // -1),
      (.rate_limits.seven_day.resets_at // 0),
      (.model.display_name // .model.id // "claude")
    ] | @tsv
  ' <<<"$payload"
)"

# ANSI color helpers (truecolor where available, fall back to 256-color codes).
RESET=$'\033[0m'
DIM=$'\033[2m'
BOLD=$'\033[1m'
GREEN=$'\033[38;5;42m'
YELLOW=$'\033[38;5;220m'
RED=$'\033[38;5;203m'
CYAN=$'\033[38;5;38m'
MAGENTA=$'\033[38;5;177m'

# Color a percentage by threshold (green <60, yellow <85, red otherwise).
color_pct() {
  local v=$1
  awk -v v="$v" 'BEGIN{ if (v<60) print "g"; else if (v<85) print "y"; else print "r" }'
}
paint() {
  case "$1" in
    g) printf '%s' "$GREEN" ;;
    y) printf '%s' "$YELLOW" ;;
    r) printf '%s' "$RED" ;;
  esac
}

# Format cost as $X.XXXX with 4 decimals (matches /usage precision).
cost_fmt=$(awk -v c="$cost" 'BEGIN{ printf "$%.4f", c }')

# Context percent as integer.
ctx_int=$(awk -v p="$ctx_pct" 'BEGIN{ printf "%d", p }')
ctx_color=$(paint "$(color_pct "$ctx_int")")

# Quota segments — only render if populated (>= 0).
quota_segment=""
if awk -v v="$h5" 'BEGIN{exit !(v>=0)}'; then
  h5_int=$(awk -v p="$h5" 'BEGIN{ printf "%d", p }')
  h5_color=$(paint "$(color_pct "$h5_int")")
  quota_segment+=" ${DIM}|${RESET} ${MAGENTA}5h${RESET} ${h5_color}${h5_int}%${RESET}"
fi
if awk -v v="$d7" 'BEGIN{exit !(v>=0)}'; then
  d7_int=$(awk -v p="$d7" 'BEGIN{ printf "%d", p }')
  d7_color=$(paint "$(color_pct "$d7_int")")
  quota_segment+=" ${DIM}|${RESET} ${MAGENTA}7d${RESET} ${d7_color}${d7_int}%${RESET}"
fi

# Token totals (input + cache) — useful sanity check next to context %.
tok_total=$(( in_tok + out_tok + cache_r + cache_c ))
tok_human=$(awk -v n="$tok_total" 'BEGIN{
  if (n>=1e6) printf "%.1fM", n/1e6;
  else if (n>=1e3) printf "%.1fk", n/1e3;
  else printf "%d", n;
}')

printf '%b%s%b %b|%b %b%s%b %b%d%%%b %b(%s)%b%b\n' \
  "$CYAN" "$model" "$RESET" \
  "$DIM" "$RESET" \
  "$BOLD" "$cost_fmt" "$RESET" \
  "$ctx_color" "$ctx_int" "$RESET" \
  "$DIM" "$tok_human" "$RESET" \
  "$quota_segment"
