#!/bin/sh

# mise/launchd の PATH でもユーザー配置と Homebrew のツールを利用する。
export PATH="$HOME/.local/bin:${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}:/opt/homebrew/bin:/usr/local/bin"

exec dotenvx run --quiet --strict --no-armor -f "$HOME/.config/.env" -fk /dev/null -- "$@"
