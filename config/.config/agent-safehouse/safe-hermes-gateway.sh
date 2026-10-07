#!/bin/bash
# launchd から safehouse 経由で hermes gateway を起動するラッパー。
# hermes.fish + __safehouse_args.fish の bash 版。



# 別ユーザー用の TMPDIR を継承しても Safehouse の mktemp を失敗させない。
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

# launchd は対話 fish の shell-init.fish を読まないため、ブラウザー用の環境値を補う。
# agent-safehouse 内で Chrome の内側 sandbox 初期化が失敗するため --no-sandbox 系を渡す。
export AGENT_BROWSER_ARGS="--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
export AGENT_BROWSER_PROFILE="$HOME/.config/agent-browser/profile"

args=(
  --workdir="$HOME/.hermes"
  --env
  --add-dirs="$HOME"
  --allow-profile-writes
  --enable=macos-gui,ssh,agent-browser,docker,all-agents,wide-read,keychain,process-control
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
  "$HOME/.local/libexec/hermes" --profile default gateway run
