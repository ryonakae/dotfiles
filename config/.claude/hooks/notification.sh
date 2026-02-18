#!/bin/sh

# Claude Code Notification hook
# stdin から JSON を受け取り、terminal-notifier で macOS 通知を送信する

# プロセスツリーを辿り、最初に見つかったmacOSアプリのBundle Identifierを返す
find_app_from_pid() {
  pid="$1"
  while [ "$pid" -gt 1 ] 2>/dev/null; do
    exe=$(ps -ww -o command= -p "$pid" 2>/dev/null | sed 's/^[[:space:]]*//')
    case "$exe" in
      */Contents/MacOS/*)
        app_bundle="${exe%/Contents/MacOS/*}"
        bundle_id=$(defaults read "${app_bundle}/Contents/Info" CFBundleIdentifier 2>/dev/null)
        if [ -n "$bundle_id" ]; then
          echo "$bundle_id"
          return 0
        fi
        ;;
    esac
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
  done
  return 1
}

# tmux, zellij などでプロセスツリーが切断されている場合のフォールバック
detect_terminal_app() {
  find_app_from_pid "$$" && return

  if [ -n "$TERM_PROGRAM" ]; then
    bundle_id=$(osascript -e "id of app \"$TERM_PROGRAM\"" 2>/dev/null)
    if [ -n "$bundle_id" ]; then
      echo "$bundle_id"
      return 0
    fi
  fi
}

INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | jq -r '.message // "Claude Code"')
TITLE=$(echo "$INPUT" | jq -r '.title // "Claude Code"')
ACTIVATE_APP=$(detect_terminal_app)

if [ -n "$ACTIVATE_APP" ]; then
  terminal-notifier \
    -title "$TITLE" \
    -message "$MESSAGE" \
    -sound default \
    -activate "$ACTIVATE_APP"
else
  terminal-notifier \
    -title "$TITLE" \
    -message "$MESSAGE" \
    -sound default
fi
