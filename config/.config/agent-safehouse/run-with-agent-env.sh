#!/bin/sh

# launchd does not activate mise; shims retain the child's project-specific selection.
export PATH="$HOME/.local/bin:${MISE_DATA_DIR:-$HOME/.local/share/mise}/shims:${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}:/opt/homebrew/bin:/usr/local/bin"

exec "/opt/homebrew/bin/dotenvx" run --quiet --strict --no-armor -f "$HOME/.config/.env" -fk /dev/null -- "$@"
