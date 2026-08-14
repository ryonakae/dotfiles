#!/bin/sh
set -eu
ALLOWED_DIRS="$HOME/.config:$HOME/.cache:$HOME/Dev"
export ALLOWED_DIRS
exec gateway "$@"
