#!/bin/bash
# launchd から safehouse 経由で hermes dashboard を起動するラッパー。
# gateway とは独立 service として動かし、Docker で ~/.hermes を共有しない。

OVERRIDES="$HOME/.config/agent-safehouse/local-overrides.sb"

# シェル履歴汚染を抑制 (~/.zsh_history などへの書き込み denied 警告も同時に消える)。
export HISTFILE=/dev/null

# launchd 起動は fish の config.fish を経由しないため、Hermes runtime に必要な
# cache/env を明示する。機密ではない実行環境値は .env ではなく wrapper に置く。
export UV_CACHE_DIR="$HOME/.hermes/cache/uv"
export PIP_CACHE_DIR="$HOME/.hermes/cache/pip"

# Docker 時代と同じく Dashboard は全インターフェースで待ち受ける。
# Mac mini は LAN 内に閉じ、iPhone からは Tailscale Serve 経由で見る。
export HERMES_DASHBOARD_HOST="${HERMES_DASHBOARD_HOST:-0.0.0.0}"
export HERMES_DASHBOARD_PORT="${HERMES_DASHBOARD_PORT:-9120}"

args=(
  --workdir="$HOME/.hermes"
  --env-pass=DISABLE_AUTOUPDATER
  --env-pass=NO_BROWSER
  --env-pass=TERM_PROGRAM
  --env-pass=SSH_AUTH_SOCK
  --env-pass=HISTFILE
  --env-pass=UV_CACHE_DIR
  --env-pass=PIP_CACHE_DIR
  --env-pass=HERMES_DASHBOARD_HOST
  --env-pass=HERMES_DASHBOARD_PORT
  --enable=ssh,docker,all-agents,wide-read,keychain
)

# cwd 外の頻出 path を rw で開ける (__safehouse_args.fish と同期、allowlist 型)。
# top-level ごとに列挙し、safehouse 既定の ~/.ssh deny 等を保つ。
# ~/.hermes は local-overrides.sb 側で信頼境界として allow されている前提。
for dir in \
  "$HOME/.com.moomoo.OpenD" \
  "$HOME/.config" \
  "$HOME/.local" \
  "$HOME/.cache" \
  "$HOME/.shepherd" \
  "$HOME/Library/Caches" \
  "$HOME/dotfiles"; do
  [ -d "$dir" ] && args+=(--add-dirs="$dir")
done
[ -d "$HOME/Dev" ] && args+=(--add-dirs="$HOME/Dev")
[ -f "$OVERRIDES" ] && args+=(--append-profile="$OVERRIDES")

exec safehouse "${args[@]}" -- hermes dashboard \
  --host "$HERMES_DASHBOARD_HOST" \
  --port "$HERMES_DASHBOARD_PORT" \
  --no-open \
  --insecure
