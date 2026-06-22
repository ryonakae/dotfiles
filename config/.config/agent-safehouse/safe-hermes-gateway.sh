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
  --enable=macos-gui,ssh,agent-browser,docker,all-agents,wide-read,keychain
)

# cwd 外の頻出 path を rw で開ける (__safehouse_args.fish と同期、allowlist 型)。
# top-level ごとに列挙し、safehouse 既定の ~/.ssh deny 等を保つ。
# ~/.hermes は信頼境界として deny を貫通させるため local-overrides.sb の allow 側に書く。
for dir in \
  "$HOME/.com.moomoo.OpenD" \
  "$HOME/.config" \
  "$HOME/.local" \
  "$HOME/.cache" \
  "$HOME/Library/Caches" \
  "$HOME/dotfiles"; do
  [ -d "$dir" ] && args+=(--add-dirs="$dir")
done
[ -d "$HOME/Dev" ] && args+=(--add-dirs="$HOME/Dev")

# 機密ファイルの deny ルール
[ -f "$OVERRIDES" ] && args+=(--append-profile="$OVERRIDES")

exec safehouse "${args[@]}" -- hermes --profile default gateway run
