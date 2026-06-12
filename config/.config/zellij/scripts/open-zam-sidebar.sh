#!/bin/sh
set -eu

zam_url="${ZAM_PLUGIN_URL:-file:$HOME/.config/zellij/plugins/zam.wasm}"
sidebar_width="${ZAM_SIDEBAR_WIDTH:-32}"
sidebar_title="${ZAM_SIDEBAR_TITLE:-ZAM Sidebar}"
in_place="${ZAM_SIDEBAR_IN_PLACE:-0}"
mode="${ZAM_SIDEBAR_MODE:-wrapper}"

if [ "$mode" = "wrapper" ]; then
  script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
  wrapper="$script_dir/open-zam-sidebar-wrapper.sh"
  if [ -x "$wrapper" ]; then
    exec "$wrapper"
  fi
  echo "open-zam-sidebar-wrapper.sh is not executable: $wrapper" >&2
  exit 1
fi

shell_quote() {
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\\\''/g")"
}

panes_json="$(zellij action list-panes --json --all --tab --state 2>/dev/null || printf '[]')"

sidebar_ids="$(
  printf '%s' "$panes_json" \
    | jq -r --arg url "$zam_url" --arg title "$sidebar_title" \
      '.[] | select(.is_plugin and .title == $title and ((.plugin_url // "") == $url)) | "plugin_\(.id)"'
)"

if [ -n "$sidebar_ids" ]; then
  printf '%s\n' "$sidebar_ids" | while IFS= read -r pane_id; do
    [ -n "$pane_id" ] && zellij action close-pane --pane-id "$pane_id" >/dev/null 2>&1 || true
  done
  exit 0
fi

url_arg="$(shell_quote "$zam_url")"
config_arg="$(shell_quote "role=sidebar-ui,sidebar_width=$sidebar_width")"
launch_cmd="plugin_id=\"\$(zellij action launch-plugin --in-place --close-replaced-pane --configuration $config_arg $url_arg)\"; zellij action move-pane --pane-id \"\$plugin_id\" left >/dev/null 2>&1 || true; sleep 3"

if [ "$in_place" = "1" ]; then
  sh -lc "$launch_cmd" >/dev/null 2>&1 || true
else
  zellij action new-pane \
    --direction right \
    --name zam-sidebar-launcher \
    -- sh -lc "$launch_cmd" >/dev/null 2>&1 || true
fi
