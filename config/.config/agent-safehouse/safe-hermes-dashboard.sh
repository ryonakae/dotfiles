#!/bin/bash
# gateway とは独立 service として動かし、Docker で ~/.hermes を共有しない。

if [ ! -d "${TMPDIR:-}" ] || [ ! -w "$TMPDIR" ] || [ ! -x "$TMPDIR" ]; then
  TMPDIR="$(getconf DARWIN_USER_TEMP_DIR)"
  if [ ! -d "$TMPDIR" ] || [ ! -w "$TMPDIR" ] || [ ! -x "$TMPDIR" ]; then
    printf '%s\n' 'error: no usable user temporary directory.' >&2
    exit 1
  fi
  export TMPDIR
fi

# シェル履歴汚染を抑制 (~/.zsh_history などへの書き込み denied 警告も同時に消える)。
export HISTFILE=/dev/null

# launchd は対話 fish の shell-init.fish を読まないため、キャッシュ用の環境値を補う。
# 機密ではない実行環境値は .env ではなく wrapper に置く。
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
  --enable=ssh,docker,all-agents,wide-read,keychain,process-control
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

exec "$HOME/.config/agent-safehouse/run-with-agent-env.sh" "/opt/homebrew/bin/safehouse" "${args[@]}" -- \
  "$HOME/.local/libexec/hermes" --profile default dashboard \
  --host "$HERMES_DASHBOARD_HOST" \
  --port "$HERMES_DASHBOARD_PORT" \
  --no-open
