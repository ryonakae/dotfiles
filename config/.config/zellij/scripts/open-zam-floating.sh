#!/bin/sh
set -eu

zam_url="${ZAM_PLUGIN_URL:-file:$HOME/Dev/private/zellij-agents-manager/target/wasm32-wasip1/release/zam.wasm}"
x="${1:-${ZAM_FLOAT_X:-5%}}"
y="${2:-${ZAM_FLOAT_Y:-5%}}"
width="${3:-${ZAM_FLOAT_WIDTH:-90%}}"
height="${4:-${ZAM_FLOAT_HEIGHT:-90%}}"

find_zam_pane() {
  zellij action list-panes --json -a 2>/dev/null \
    | jq -r --arg url "$zam_url" '[.[] | select(.is_plugin and ((.plugin_url // "") == $url)) | "plugin_\(.id)"] | last // empty'
}

pane_id="$(zellij action launch-or-focus-plugin --floating --move-to-focused-tab "$zam_url" 2>/dev/null || true)"

case "$pane_id" in
  plugin_*) ;;
  *)
    pane_id=""
    for _ in 1 2 3 4 5; do
      pane_id="$(find_zam_pane)"
      [ -n "$pane_id" ] && break
      sleep 0.1
    done
    ;;
esac

if [ -n "$pane_id" ]; then
  zellij action show-floating-panes >/dev/null 2>&1 || true
  zellij action change-floating-pane-coordinates \
    --pane-id "$pane_id" \
    --x "$x" \
    --y "$y" \
    --width "$width" \
    --height "$height"
  zellij action focus-pane-id "$pane_id" >/dev/null 2>&1 || true
fi
