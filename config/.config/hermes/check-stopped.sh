#!/bin/bash
set -euo pipefail

fail() {
  printf 'Hermes: %s\n' "$1" >&2
  exit 1
}

# A different bootstrap namespace can hide the user's registered services.
manager=$(/bin/launchctl managername) || fail 'cannot inspect the launchd session.'
[[ "$manager" == Aqua ]] || fail 'run activation from the user GUI session.'
jobs=$(/bin/launchctl list) || fail 'cannot list launchd services.'
[[ "${jobs%%$'\n'*}" == $'PID\tStatus\tLabel' ]] || fail 'unknown launchd list format.'
while read -r pid status label extra; do
  [[ "$pid" == PID ]] && continue
  [[ "$pid" =~ ^(-|[0-9]+)$ && "$status" =~ ^-?[0-9]+$ && -n "$label" && -z "$extra" ]] \
    || fail 'unknown launchd service record.'
  case "$label" in
    ai.hermes.gateway|ai.hermes.gateway.*|ai.hermes.dashboard|ai.hermes.dashboard.*)
      fail 'service is still loaded; stop it with hermes-gateway / hermes-dashboard before applying.'
      ;;
  esac
done <<< "$jobs"

# Native status commands may repair stale files; inspect processes without invoking Hermes.
processes=$(/bin/ps -ww -U "$(/usr/bin/id -u)" -o command=) \
  || fail 'cannot inspect user processes.'
[[ -n "$processes" ]] || fail 'empty process inventory.'
pattern='(^|[ /])(\.?hermes(-agent)?(-wrapped)?|gateway/run\.py|hermes_cli/(main|main_dashboard)\.py)([[:space:]]|$)|(^|[[:space:]])-m[[:space:]]+(hermes_cli([.[:space:]]|$)|gateway\.run([[:space:]]|$))'
while IFS= read -r process; do
  if [[ "$process" =~ $pattern ]]; then
    fail 'a Hermes process is still present; stop Hermes before applying.'
  fi
done <<< "$processes"
exit 0
