#!/bin/bash
# launchd から safehouse 経由で hermes gateway を起動するラッパー。
# hermes.fish + __safehouse_args.fish の bash 版。

OVERRIDES="$HOME/.config/agent-safehouse/local-overrides.sb"

# シェル履歴汚染を抑制 (~/.zsh_history などへの書き込み denied 警告も同時に消える)。
export HISTFILE=/dev/null

# launchd 起動は fish の config.fish を経由しないため、対話 fish セッションで
# global export している agent-browser 系の env をここでも明示的に export する。
# agent-safehouse 内で Chrome の内側 sandbox 初期化が失敗するため --no-sandbox 系を渡す。
export AGENT_BROWSER_ARGS="--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
export AGENT_BROWSER_PROFILE="$HOME/.config/agent-browser/profile"

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
  --enable=macos-gui,ssh,agent-browser,docker,wide-read,keychain
)

# HOME 全体を rw (__safehouse_args.fish と同期、denylist 型)。
# 機密 / 個人 dir / Library 配下 credential は local-overrides.sb で後勝ち deny。
# ~/.hermes は信頼境界として deny を貫通させるため local-overrides.sb の allow 側に書く。
args+=(--add-dirs="$HOME")

# 機密ファイルの deny ルール
[ -f "$OVERRIDES" ] && args+=(--append-profile="$OVERRIDES")

exec safehouse "${args[@]}" -- hermes gateway run
