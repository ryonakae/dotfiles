#!/bin/bash
# launchd から safehouse 経由で hermes dashboard を起動するラッパー。
# gateway とは独立 service として動かし、Docker で ~/.hermes を共有しない。

OVERRIDES="$HOME/.config/agent-safehouse/local-overrides.sb"

# シェル履歴汚染を抑制 (~/.zsh_history などへの書き込み denied 警告も同時に消える)。
export HISTFILE=/dev/null

# Hermes セッション内 marker。子プロセスが Hermes runtime 由来だと判別できるようにする。
export HERMES_AGENT=1

# launchd 起動は fish の config.fish を経由しないため、Hermes runtime に必要な
# cache/env を明示する。機密ではない実行環境値は .env ではなく wrapper に置く。
export UV_CACHE_DIR="$HOME/.hermes/cache/uv"
export PIP_CACHE_DIR="$HOME/.hermes/cache/pip"

# Dashboard 本体は localhost-only のままにし、iPhone/Tailscale からは
# 下の Host rewrite proxy 経由で見る。DB と secrets を扱うため、本体を
# Tailnet/LAN に直接 bind しない。
export HERMES_DASHBOARD_HOST="${HERMES_DASHBOARD_HOST:-127.0.0.1}"
export HERMES_DASHBOARD_PORT="${HERMES_DASHBOARD_PORT:-9119}"
export HERMES_DASHBOARD_PROXY_HOST="${HERMES_DASHBOARD_PROXY_HOST:-127.0.0.1}"
export HERMES_DASHBOARD_PROXY_PORT="${HERMES_DASHBOARD_PROXY_PORT:-9120}"
export HERMES_DASHBOARD_UPSTREAM_HOST="$HERMES_DASHBOARD_HOST"
export HERMES_DASHBOARD_UPSTREAM_PORT="$HERMES_DASHBOARD_PORT"

args=(
  --workdir="$HOME/.hermes"
  --env-pass=DISABLE_AUTOUPDATER
  --env-pass=NO_BROWSER
  --env-pass=TERM_PROGRAM
  --env-pass=SSH_AUTH_SOCK
  --env-pass=HISTFILE
  --env-pass=HERMES_AGENT
  --env-pass=UV_CACHE_DIR
  --env-pass=PIP_CACHE_DIR
  --env-pass=HERMES_DASHBOARD_HOST
  --env-pass=HERMES_DASHBOARD_PORT
  --env-pass=HERMES_DASHBOARD_PROXY_HOST
  --env-pass=HERMES_DASHBOARD_PROXY_PORT
  --env-pass=HERMES_DASHBOARD_UPSTREAM_HOST
  --env-pass=HERMES_DASHBOARD_UPSTREAM_PORT
  --enable=ssh,docker,all-agents,wide-read,keychain
)

# cwd 外の頻出 path を rw で開ける。dashboard は config/env/session/log へアクセスする。
# ~/.hermes は local-overrides.sb 側で信頼境界として allow されている前提。
for dir in \
  "$HOME/.config" \
  "$HOME/.local" \
  "$HOME/.cache" \
  "$HOME/Library" \
  "$HOME/dotfiles"; do
  [ -d "$dir" ] && args+=(--add-dirs="$dir")
done

[ -d "$HOME/Dev" ] && args+=(--add-dirs="$HOME/Dev")
[ -f "$OVERRIDES" ] && args+=(--append-profile="$OVERRIDES")

exec safehouse "${args[@]}" -- bash -lc '
proxy_pid=""
cleanup() {
  if [ -n "$proxy_pid" ]; then
    kill "$proxy_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

python3 "$HOME/.config/agent-safehouse/hermes-dashboard-host-proxy.py" &
proxy_pid=$!

hermes dashboard \
  --host "$HERMES_DASHBOARD_HOST" \
  --port "$HERMES_DASHBOARD_PORT" \
  --no-open
'
