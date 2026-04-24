#!/bin/bash
# launchd から safehouse 経由で hermes gateway を起動するラッパー。
# hermes.fish + __safehouse_args.fish の bash 版。

DOTFILES_DIR="$HOME/dotfiles"
OVERRIDES="$HOME/.config/agent-safehouse/local-overrides.sb"
HERMES_OVERRIDES="$HOME/.config/agent-safehouse/hermes-overrides.sb"

args=(
  --workdir="$HOME/.hermes"
  --env-pass=CONTEXT7_API_KEY
  --env-pass=DISABLE_AUTOUPDATER
  --env-pass=NO_BROWSER
  --env-pass=TERM_PROGRAM
  --enable=macos-gui,ssh,cleanshot,agent-browser,docker,clipboard
)

# dotfiles を read-write で許可（__safehouse_args では ro だが Hermes Agent は rw）
if [ -d "$DOTFILES_DIR" ]; then
  args+=(--add-dirs="$DOTFILES_DIR")
fi

# 機密ファイルの deny ルール
[ -f "$OVERRIDES" ] && args+=(--append-profile="$OVERRIDES")

# rw
args+=(
  --add-dirs="$HOME/.hermes"
  --add-dirs="$HOME/.local/state/hermes"
  --add-dirs="$HOME/Dev/private"
)

# ro
args+=(
  --add-dirs-ro="$HOME/.local/bin"
  --add-dirs-ro=/usr/local/bin
  --add-dirs-ro="/Applications/Docker.app"
)

# Hermes Agent 専用 deny ルール
[ -f "$HERMES_OVERRIDES" ] && args+=(--append-profile="$HERMES_OVERRIDES")

exec safehouse "${args[@]}" -- hermes gateway run
