#!/bin/sh

set -eu

direction=${1-}
case "$direction" in
  left|right) ;;
  *)
    echo "usage: focus-pane-or-tab.sh <left|right>" >&2
    exit 2
    ;;
esac

if [ -z "${HERDR_ACTIVE_WORKSPACE_ID:-}" ] ||
  [ -z "${HERDR_ACTIVE_TAB_ID:-}" ] ||
  [ -z "${HERDR_ACTIVE_PANE_ID:-}" ]; then
  echo "error: Herdr active context is unavailable" >&2
  exit 1
fi

herdr_bin=${HERDR_BIN_PATH:-herdr}
neighbor_json=$(
  "$herdr_bin" pane neighbor \
    --direction "$direction" \
    --pane "$HERDR_ACTIVE_PANE_ID"
)
neighbor_id=$(printf '%s\n' "$neighbor_json" | jq -r '.result.neighbor.neighbor_pane_id // empty')

if [ -n "$neighbor_id" ]; then
  "$herdr_bin" pane focus \
    --direction "$direction" \
    --pane "$HERDR_ACTIVE_PANE_ID" >/dev/null
  exit 0
fi

tabs_json=$("$herdr_bin" tab list --workspace "$HERDR_ACTIVE_WORKSPACE_ID")
target_tab_id=$(printf '%s\n' "$tabs_json" | jq -er \
  --arg active "$HERDR_ACTIVE_TAB_ID" \
  --arg direction "$direction" '
    .result.tabs as $tabs
    | ($tabs | map(.tab_id) | index($active)) as $index
    | ($tabs | length) as $length
    | if $length == 0 or $index == null then
        empty
      elif $direction == "left" then
        $tabs[(($index - 1 + $length) % $length)].tab_id
      else
        $tabs[(($index + 1) % $length)].tab_id
      end
  ')

if [ "$target_tab_id" = "$HERDR_ACTIVE_TAB_ID" ]; then
  exit 0
fi

"$herdr_bin" tab focus "$target_tab_id" >/dev/null
