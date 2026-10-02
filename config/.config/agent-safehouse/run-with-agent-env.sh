#!/bin/sh

# mise/launchd の PATH でも rm 転送と Homebrew のツールを利用する。
export PATH="$HOME/.local/bin:${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}:/opt/homebrew/bin:/usr/local/bin"

if [ ! -x "$HOME/.local/bin/rm" ]; then
  printf '%s\n' 'error: managed rm wrapper is missing; deploy dotfiles first.' >&2
  exit 127
fi

exec dotenvx run --quiet --strict --no-armor -f "$HOME/.config/.env" -fk /dev/null -- "$@"
