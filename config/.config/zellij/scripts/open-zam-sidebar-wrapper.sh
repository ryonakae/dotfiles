#!/bin/sh
set -eu

zam_url="${ZAM_PLUGIN_URL:-file:$HOME/.config/zellij/plugins/zam.wasm}"
sidebar_width="${ZAM_SIDEBAR_WIDTH:-20%}"
plugin_sidebar_width="${ZAM_SIDEBAR_PLUGIN_WIDTH:-32}"
sidebar_title="${ZAM_SIDEBAR_TITLE:-ZAM Sidebar}"
width_tolerance="${ZAM_SIDEBAR_WIDTH_TOLERANCE:-4}"
resize_step_columns="${ZAM_SIDEBAR_RESIZE_STEP_COLUMNS:-8}"
layout_root="${ZAM_SIDEBAR_LAYOUT_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/zam/sidebar-layouts}"
dump_file="${ZAM_SIDEBAR_DUMP_FILE:-}"
dry_run="${ZAM_SIDEBAR_DRY_RUN:-0}"
in_place="${ZAM_SIDEBAR_IN_PLACE:-0}"

json_quote() {
  jq -Rn --arg v "$1" '$v'
}

shell_quote() {
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\\\''/g")"
}

is_percent_width() {
  case "$1" in
    *%) return 0 ;;
    *) return 1 ;;
  esac
}

layout_size_arg() {
  if is_percent_width "$1"; then
    printf '"%s"' "$1"
  else
    printf '%s' "$1"
  fi
}

plugin_width_arg() {
  if is_percent_width "$1"; then
    printf '%s' "$plugin_sidebar_width"
  else
    printf '%s' "$1"
  fi
}

safe_name() {
  printf '%s' "$1" | tr -c 'A-Za-z0-9_.-' '_'
}

current_tab_id() {
  zellij action current-tab-info 2>/dev/null | awk -F': ' '$1 == "id" { print $2; exit }'
}

focused_tab_id() {
  zellij action list-panes --json --all --tab --state 2>/dev/null \
    | jq -r '.[] | select(.is_focused) | .tab_id' \
    | head -n 1
}

current_session_name() {
  if [ -n "${ZELLIJ_SESSION_NAME:-}" ]; then
    printf '%s' "$ZELLIJ_SESSION_NAME"
    return
  fi
  zellij list-sessions -s -n 2>/dev/null | head -n 1
}

close_active_tab_sidebars() {
  panes_json="$(zellij action list-panes --json --all --tab --state 2>/dev/null || printf '[]')"
  ids="$(
    printf '%s' "$panes_json" \
      | jq -r --arg url "$zam_url" --arg title "$sidebar_title" --argjson tab_id "$1" \
        '.[] | select(.tab_id == $tab_id and .is_plugin and (.title == $title or ((.plugin_url // "") == $url))) | "plugin_\(.id)"'
  )"

  [ -z "$ids" ] && return 1
  printf '%s\n' "$ids" | while IFS= read -r pane_id; do
    [ -n "$pane_id" ] && zellij action close-pane --pane-id "$pane_id" >/dev/null 2>&1 || true
  done
  return 0
}

close_launcher_panes() {
  panes_json="$(zellij action list-panes --json --all --tab --state 2>/dev/null || printf '[]')"
  printf '%s' "$panes_json" \
    | jq -r '.[] | select((.title // "") == "zam-sidebar-launcher") | if .is_plugin then "plugin_\(.id)" else "terminal_\(.id)" end' \
    | while IFS= read -r pane_id; do
      [ -n "$pane_id" ] && zellij action close-pane --pane-id "$pane_id" >/dev/null 2>&1 || true
    done
}

fallback_legacy_sidebar() {
  url_arg="$(shell_quote "$zam_url")"
  config_arg="$(shell_quote "role=sidebar-ui,sidebar_width=$(plugin_width_arg "$sidebar_width")")"
  launch_cmd='plugin_id="$(zellij action launch-plugin --in-place --close-replaced-pane --configuration '"$config_arg"' '"$url_arg"')";
for _ in 1 2 3; do
  zellij action move-pane --pane-id "$plugin_id" left >/dev/null 2>&1 && break
  sleep 0.01
done
sleep 0.5'
  if [ "$in_place" = "1" ]; then
    sh -lc "$launch_cmd" >/dev/null 2>&1 || true
    return
  fi
  zellij action new-pane \
    --direction right \
    --name zam-sidebar-launcher \
    -- sh -lc "$launch_cmd" >/dev/null 2>&1 || true
}

active_tab_sidebar_geometry() {
  panes_json="$(zellij action list-panes --json --all --tab --state --geometry 2>/dev/null || printf '[]')"
  printf '%s' "$panes_json" \
    | jq -r --arg url "$zam_url" --arg title "$sidebar_title" --argjson tab_id "$1" '
      .[]
      | select(.tab_id == $tab_id and .is_plugin and (.is_floating | not))
      | select(.title == $title or ((.plugin_url // "") == $url))
      | ["plugin_\(.id)", .pane_columns]
      | @tsv
    ' \
    | head -n 1
}

active_tab_total_columns() {
  panes_json="$(zellij action list-panes --json --all --tab --state --geometry 2>/dev/null || printf '[]')"
  printf '%s' "$panes_json" \
    | jq -r --argjson tab_id "$1" '
      [
        .[]
        | select(.tab_id == $tab_id and (.is_floating | not))
        | (.pane_x + .pane_columns)
      ]
      | max // empty
    '
}

target_sidebar_columns() {
  spec="$1"
  tab_id="$2"
  if is_percent_width "$spec"; then
    pct="${spec%\%}"
    total_cols="$(active_tab_total_columns "$tab_id")"
    [ -z "$total_cols" ] && return 1
    awk -v total="$total_cols" -v pct="$pct" 'BEGIN { printf "%d\n", int((total * pct / 100) + 0.999) }'
  else
    printf '%s\n' "$spec"
  fi
}

max_sidebar_columns() {
  spec="$1"
  tolerance="$2"
  tab_id="$3"
  if is_percent_width "$spec"; then
    pct="${spec%\%}"
    total_cols="$(active_tab_total_columns "$tab_id")"
    [ -z "$total_cols" ] && return 1
    awk -v total="$total_cols" -v pct="$pct" -v tol="$tolerance" 'BEGIN { printf "%d\n", int((total * pct / 100) + tol + 0.999) }'
  else
    printf '%s\n' "$((spec + tolerance))"
  fi
}

adjust_active_tab_sidebar_width() {
  tab_id="$1"
  spec="$2"
  tolerance="$3"
  max_cols="$(max_sidebar_columns "$spec" "$tolerance" "$tab_id" || true)"
  [ -z "$max_cols" ] && return 0

  for _ in 1 2 3 4 5 6 7 8 9 10; do
    geometry="$(active_tab_sidebar_geometry "$tab_id")"
    [ -n "$geometry" ] && break
    sleep 0.1
  done

  [ -z "${geometry:-}" ] && return 0
  pane_id="$(printf '%s' "$geometry" | awk '{ print $1 }')"

  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24; do
    geometry="$(active_tab_sidebar_geometry "$tab_id")"
    cols="$(printf '%s' "$geometry" | awk '{ print $2 }')"
    [ -z "$cols" ] && return 0
    [ "$cols" -le "$max_cols" ] && return 0
    zellij action resize --pane-id "$pane_id" decrease right >/dev/null 2>&1 || return 0
    sleep 0.05
  done
}

extract_active_tab() {
  awk '
    function brace_delta(line, tmp, opens, closes) {
      tmp = line
      opens = gsub(/\{/, "{", tmp)
      tmp = line
      closes = gsub(/\}/, "}", tmp)
      return opens - closes
    }
    /^[[:space:]]*tab[[:space:]].*focus=true.*\{/ && !in_tab {
      print
      in_tab = 1
      depth = brace_delta($0)
      next
    }
    in_tab {
      depth += brace_delta($0)
      if (depth == 0) {
        exit
      }
      print
    }
  ' "$1"
}

strip_frame_plugins() {
  awk '
    function brace_delta(line, tmp, opens, closes) {
      tmp = line
      opens = gsub(/\{/, "{", tmp)
      tmp = line
      closes = gsub(/\}/, "}", tmp)
      return opens - closes
    }
    function flush_block(i) {
      if (!skip_block) {
        for (i = 1; i <= block_len; i++) {
          print block[i]
        }
      }
      block_len = 0
      block_depth = 0
      skip_block = 0
      in_block = 0
    }
    /^        pane([[:space:]].*)?(\{)?[[:space:]]*$/ && !in_block {
      in_block = 1
      block_len = 1
      block[1] = $0
      block_depth = brace_delta($0)
      if (block_depth == 0) {
        flush_block()
      }
      next
    }
    /^        floating_panes[[:space:]]*\{/ && !in_block {
      in_block = 1
      block_len = 1
      block[1] = $0
      block_depth = brace_delta($0)
      skip_block = 1
      next
    }
    in_block {
      block[++block_len] = $0
      if ($0 ~ /plugin location="zellij:(tab-bar|status-bar|compact-bar)"/) {
        skip_block = 1
      }
      block_depth += brace_delta($0)
      if (block_depth == 0) {
        flush_block()
      }
      next
    }
    { print }
  '
}

normalize_retained_terminal_panes() {
  awk '
    function brace_delta(line, tmp, opens, closes) {
      tmp = line
      opens = gsub(/\{/, "{", tmp)
      tmp = line
      closes = gsub(/\}/, "}", tmp)
      return opens - closes
    }
    function normalized_pane(line, indent, out, size_token) {
      indent = line
      sub(/pane.*/, "", indent)
      out = indent "pane"
      if (line ~ /focus=true/) {
        out = out " focus=true"
      }
      if (match(line, /size=("[^"]+"|[0-9]+%?)/)) {
        size_token = substr(line, RSTART, RLENGTH)
        out = out " " size_token
      }
      return out
    }
    skip_terminal_block {
      terminal_depth += brace_delta($0)
      if (terminal_depth == 0) {
        skip_terminal_block = 0
      }
      next
    }
    /^[[:space:]]*pane[[:space:]].*\{/ && $0 ~ /(command=|cwd=)/ && $0 !~ /split_direction=/ {
      print normalized_pane($0)
      terminal_depth = brace_delta($0)
      if (terminal_depth > 0) {
        skip_terminal_block = 1
      }
      next
    }
    /^[[:space:]]*pane[[:space:]].*$/ && $0 !~ /\{/ && $0 ~ /(command=|cwd=)/ {
      print normalized_pane($0)
      next
    }
    { print }
  '
}

indent_body() {
  sed 's/^/                /'
}

generate_layout() {
  source_dump="$1"
  active_tab="$(mktemp "${TMPDIR:-/tmp}/zam-active-tab.XXXXXX")"
  body="$(mktemp "${TMPDIR:-/tmp}/zam-active-body.XXXXXX")"
  extract_active_tab "$source_dump" > "$active_tab"
  if [ ! -s "$active_tab" ]; then
    rm -f "$active_tab" "$body"
    return 1
  fi

  tab_line="$(sed -n '1p' "$active_tab")"
  sed '1d' "$active_tab" | strip_frame_plugins | normalize_retained_terminal_panes > "$body"
  url_json="$(json_quote "$zam_url")"
  sidebar_size="$(layout_size_arg "$sidebar_width")"
  sidebar_plugin_width="$(plugin_width_arg "$sidebar_width")"

  printf 'layout {\n'
  printf '%s\n' "$tab_line"
  printf '        pane size=1 borderless=true {\n'
  printf '            plugin location="zellij:tab-bar"\n'
  printf '        }\n'
  printf '        pane split_direction="vertical" {\n'
  printf '            pane size=%s {\n' "$sidebar_size"
  printf '                plugin location=%s {\n' "$url_json"
  printf '                    role "sidebar-ui"\n'
  printf '                    sidebar_width "%s"\n' "$sidebar_plugin_width"
  printf '                }\n'
  printf '            }\n'
  printf '            pane {\n'
  indent_body < "$body"
  printf '            }\n'
  printf '        }\n'
  printf '        pane size=1 borderless=true {\n'
  printf '            plugin location="zellij:status-bar"\n'
  printf '        }\n'
  printf '    }\n'
  printf '}\n'

  rm -f "$active_tab" "$body"
}

fallback_and_finish() {
  if [ "$dry_run" = "1" ]; then
    echo "failed to dump active Zellij layout" >&2
    exit 1
  fi

  fallback_legacy_sidebar
  if [ "$in_place" = "1" ]; then
    exit 0
  fi
  sleep 1
  close_launcher_panes
  sleep 0.2
  if [ -n "$tab_id" ]; then
    adjust_active_tab_sidebar_width "$tab_id" "$sidebar_width" "$width_tolerance"
  fi
  exit 0
}

tab_id="${ZAM_SIDEBAR_TAB_ID:-}"
if [ -z "$tab_id" ] && [ "$dry_run" != "1" ]; then
  tab_id="$(current_tab_id)"
fi
if [ -z "$tab_id" ] && [ "$dry_run" != "1" ]; then
  tab_id="$(focused_tab_id)"
fi

if [ "$dry_run" != "1" ] && [ -n "$tab_id" ] && close_active_tab_sidebars "$tab_id"; then
  exit 0
fi

if [ "$in_place" = "1" ]; then
  fallback_and_finish
fi

mkdir -p "$layout_root"
session_name="$(current_session_name || true)"
layout_prefix="$(safe_name "${session_name:-session}")-${tab_id:-active}"
before_layout="$layout_root/$layout_prefix.before.kdl"
wrapper_layout="$(mktemp "$layout_root/$layout_prefix.wrapper.XXXXXX")"

if [ -n "$dump_file" ]; then
  cp "$dump_file" "$before_layout"
else
  zellij action dump-layout > "$before_layout"
fi

if [ ! -s "$before_layout" ]; then
  fallback_and_finish
fi

generate_layout "$before_layout" > "$wrapper_layout" || fallback_and_finish

if [ "$dry_run" = "1" ]; then
  cat "$wrapper_layout"
  exit 0
fi

zellij action override-layout \
  --apply-only-to-active-tab \
  --retain-existing-terminal-panes \
  --retain-existing-plugin-panes \
  "$wrapper_layout"

if [ -n "$tab_id" ] && [ -z "$(active_tab_sidebar_geometry "$tab_id")" ]; then
  fallback_legacy_sidebar
  sleep 1
fi

if [ -n "$tab_id" ]; then
  adjust_active_tab_sidebar_width "$tab_id" "$sidebar_width" "$width_tolerance"
fi

close_launcher_panes
sleep 0.2

if [ -n "$tab_id" ]; then
  adjust_active_tab_sidebar_width "$tab_id" "$sidebar_width" "$width_tolerance"
fi
