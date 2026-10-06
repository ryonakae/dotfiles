#!/bin/sh

# launchd の最小 PATH でも、ユーザー配置と補完用 Homebrew のツールを利用する。
export PATH="$HOME/.local/bin:${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}:/opt/homebrew/bin:/usr/local/bin"

exec dotenvx run --quiet --strict --no-armor -f "$HOME/.config/.env" -fk /dev/null -- "$@"
