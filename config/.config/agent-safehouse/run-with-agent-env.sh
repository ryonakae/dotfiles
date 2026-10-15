#!/bin/sh

# launchd does not activate mise; shims retain the child's project-specific selection.
# Safehouse needs Homebrew Bash ahead of the system Bash for policy generation.
export PATH="$HOME/.local/bin:${MISE_DATA_DIR:-$HOME/.local/share/mise}/shims:/opt/homebrew/bin:${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}:/usr/local/bin"

exec "/opt/homebrew/bin/dotenvx" run --quiet --strict --no-armor -f "$HOME/.config/.env" -fk /dev/null -- "$@"
