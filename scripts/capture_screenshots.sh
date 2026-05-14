#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/docs/screenshots/final"

mkdir -p "$OUTPUT_DIR"

cat <<'INSTRUCTIONS'
Before capture:
- switch bot UI to English mode
- open only PulseMarket AI chat
- crop/select only the bot conversation area
- do not include Telegram left chat list
- do not include ChatGPT, Codex, terminal, desktop, tokens, .env, server logs
- use clean screenshots only

This script uses interactive region capture:
screencapture -i -o "docs/screenshots/final/FILE_NAME.png"

After each prompt:
1. Prepare the requested screen in Telegram.
2. Press Enter here.
3. Select only the clean PulseMarket AI bot conversation area.

INSTRUCTIONS

capture() {
  local file_name="$1"
  local instruction="$2"
  local output_path="$OUTPUT_DIR/$file_name"

  printf '\n%s\n' "$instruction"
  printf 'Capture: docs/screenshots/final/%s\n' "$file_name"
  read -r -p "Press Enter when the screen is ready..."

  rm -f "$output_path"
  screencapture -i -o "$output_path"

  if [[ -s "$output_path" ]]; then
    printf 'Saved: docs/screenshots/final/%s\n' "$file_name"
  else
    printf 'Capture was cancelled or empty: docs/screenshots/final/%s\n' "$file_name" >&2
    return 1
  fi
}

capture "01_start_menu.png" "1. Prepare /start main menu in English mode."
capture "02_hot_market.png" "2. Prepare Hot Markets with Pulse Score and Market Health."
capture "03_search_bitcoin.png" "3. Prepare Search bitcoin results."
capture "04_resolution_explainer.png" "4. Prepare Resolution Explainer."
capture "05_inline_search.png" "5. Prepare inline search: @PulseMarketAIBot bitcoin."
capture "06_watchlist.png" "6. Prepare Watchlist."
capture "07_admin_stats.png" "7. Prepare /admin_stats."
capture "08_open_polymarket_link.png" "8. Prepare Open Polymarket link flow."

cat <<'DONE'

All captures completed.
Review every PNG manually before upload or commit.
PNG files in docs/screenshots/final/ are ignored by git by default.
DONE
