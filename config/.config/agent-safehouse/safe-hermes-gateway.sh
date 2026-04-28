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
  --env-pass=AGENT_BROWSER_ARGS
  --env-pass=AGENT_BROWSER_PROFILE
  --env-pass=UV_CACHE_DIR
  --env-pass=PIP_CACHE_DIR
  --env-pass=GOOGLE_WORKSPACE_CLI_CONFIG_DIR
  --env-pass=GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND
  --env-pass=SSL_CERT_FILE
  --env-pass=SSH_AUTH_SOCK
  --enable=macos-gui,ssh,agent-browser,docker
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
  --add-dirs-ro="$HOME/.local/share/opencode"
)

# Hermes Agent 専用オーバーライド
[ -f "$HERMES_OVERRIDES" ] && args+=(--append-profile="$HERMES_OVERRIDES")

# agent-safehouse 内で Chrome の内側 sandbox 初期化が失敗するため、
# Hermes から呼ぶ agent-browser にだけ Chrome 起動引数を渡す。
# 実 Chrome プロファイル (cookie / 履歴 / 保存パスワード) と分離するため、
# agent-browser の正規オプションで専用 profile directory を指定する。
export AGENT_BROWSER_ARGS="--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
export AGENT_BROWSER_PROFILE="$HOME/.hermes/chrome-profile"

# uv/pip の既定 cache (~/.cache 配下) は sandbox の write deny に引っ掛かるため、
# rw 全面許可されている ~/.hermes 配下に隔離する。
export UV_CACHE_DIR="$HOME/.hermes/cache/uv"
export PIP_CACHE_DIR="$HOME/.hermes/cache/pip"

# Google Workspace CLI (gws) — 自律エージェント用 credential store を ~/.config/gws と分離する。
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.hermes/gws"
export GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file
export SSL_CERT_FILE=/etc/ssl/cert.pem

exec safehouse "${args[@]}" -- hermes gateway run
