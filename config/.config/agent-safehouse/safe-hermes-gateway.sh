#!/bin/bash
# launchd から safehouse 経由で hermes gateway を起動するラッパー。
# hermes.fish + __safehouse_args.fish の bash 版。

HOME_DIR="$HOME"
DOTFILES_DIR="$HOME/dotfiles"
OVERRIDES="$HOME/.config/agent-safehouse/local-overrides.sb"

args=(
  --workdir="$HOME"
  --env-pass=CONTEXT7_API_KEY
  --env-pass=DISABLE_AUTOUPDATER
  --env-pass=NO_BROWSER
  --env-pass=TERM_PROGRAM
  --enable=macos-gui,ssh,cleanshot,agent-browser,docker,clipboard
)

# dotfiles を read-only で許可
if [ -d "$DOTFILES_DIR" ]; then
  args+=(--add-dirs-ro="$DOTFILES_DIR")
fi

# 機密ファイルの deny ルール
if [ -f "$OVERRIDES" ]; then
  args+=(--append-profile="$OVERRIDES")
fi

# hermes 固有
args+=(
  --add-dirs="$HOME/.hermes"
  --add-dirs-ro="$HOME/.local/bin"
  --add-dirs="$HOME/.local/state/hermes"
  --add-dirs-ro=/usr/local/bin
  --add-dirs-ro="/Applications/Docker.app"
  --add-dirs="$HOME/Library/LaunchAgents"
)

exec safehouse "${args[@]}" -- hermes gateway run
