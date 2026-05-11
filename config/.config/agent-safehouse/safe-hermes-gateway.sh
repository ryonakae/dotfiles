#!/bin/bash
# launchd から safehouse 経由で hermes gateway を起動するラッパー。
# hermes.fish + __safehouse_args.fish の bash 版。

OVERRIDES="$HOME/.config/agent-safehouse/local-overrides.sb"

# シェル履歴汚染を抑制 (~/.zsh_history などへの書き込み denied 警告も同時に消える)。
export HISTFILE=/dev/null

# Hermes 公式に runtime 識別 marker が無いため、skill (commit-push など) が
# 「Hermes セッション内」と判別できるよう独自 marker を子プロセスへ伝搬する。
export HERMES_AGENT=1

args=(
  --workdir="$HOME/.hermes"
  --env-pass=CONTEXT7_API_KEY
  --env-pass=DISABLE_AUTOUPDATER
  --env-pass=NO_BROWSER
  --env-pass=TERM_PROGRAM
  --env-pass=AGENT_BROWSER_ARGS
  --env-pass=AGENT_BROWSER_PROFILE
  --env-pass=SSH_AUTH_SOCK
  --env-pass=HISTFILE
  --env-pass=HERMES_AGENT
  --enable=macos-gui,ssh,agent-browser,docker,all-agents,wide-read,keychain
)

# cwd 外の頻出 path を rw で開ける (__safehouse_args.fish と同期)。
for dir in \
  "$HOME/.config" \
  "$HOME/.local" \
  "$HOME/.cache" \
  "$HOME/Library" \
  "$HOME/dotfiles" \
  "$HOME/.hermes"; do
  [ -d "$dir" ] && args+=(--add-dirs="$dir")
done

[ -d "$HOME/Dev" ] && args+=(--add-dirs="$HOME/Dev")

# 機密ファイルの deny ルール
[ -f "$OVERRIDES" ] && args+=(--append-profile="$OVERRIDES")

exec safehouse "${args[@]}" -- hermes gateway run
