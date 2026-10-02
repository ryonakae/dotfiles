#!/bin/bash
# launchd から safehouse 経由で hermes dashboard を起動するラッパー。
# gateway とは独立 service として動かし、Docker で ~/.hermes を共有しない。



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
  --env
  --add-dirs="$HOME"
  --allow-profile-writes
  --enable=ssh,docker,all-agents,wide-read,keychain,process-control,launch-services
)

# HOME の許可より後に拒否を適用し、欠落時は起動を止める。
for profile in compatibility local-overrides; do
  file="$HOME/.config/agent-safehouse/$profile.sb"
  if [ ! -r "$file" ]; then
    printf 'error: required Safehouse profile is missing: %s\n' "$file" >&2
    exit 1
  fi
  args+=(--append-profile="$file")
done

# launchd でも mise のバージョン指定を適用し、Hermes 本体は既存 venv に固定する。
exec mise -C "$HOME/.hermes" exec -- "$HOME/.config/agent-safehouse/run-with-agent-env.sh" safehouse "${args[@]}" -- \
  "$HOME/.hermes/hermes-agent/venv/bin/hermes" dashboard \
  --host "$HERMES_DASHBOARD_HOST" \
  --port "$HERMES_DASHBOARD_PORT" \
  --no-open \
  --insecure
