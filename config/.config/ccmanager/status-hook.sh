#!/bin/sh

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

detect_terminal_app() {
  find_app_from_pid "$PPID" && return

  # プロセスツリーが切断されている場合（tmux, zellij等）、TERM_PROGRAMからバンドルIDを解決する
  if [ -n "$TERM_PROGRAM" ]; then
    bundle_id=$(osascript -e "id of app \"$TERM_PROGRAM\"" 2>/dev/null)
    if [ -n "$bundle_id" ]; then
      echo "$bundle_id"
      return 0
    fi
  fi
}

# 状態を人間が読みやすいメッセージに変換
get_state_message() {
  case "$1" in
    waiting_input)
      echo "Waiting for your input."
      ;;
    pending_auto_approval)
      echo "Pending auto approval."
      ;;
    *)
      echo "$1"
      ;;
  esac
}

ACTIVATE_APP=$(detect_terminal_app)
STATE_MESSAGE=$(get_state_message "$CCMANAGER_NEW_STATE")

case "$CCMANAGER_NEW_STATE" in
  waiting_input|pending_auto_approval)
    if [ -n "$ACTIVATE_APP" ]; then
      terminal-notifier \
        -title "CCManager" \
        -message "\[$CCMANAGER_WORKTREE_BRANCH] $STATE_MESSAGE" \
        -sound default \
        -activate "$ACTIVATE_APP"
    else
      terminal-notifier \
        -title "CCManager" \
        -message "\[$CCMANAGER_WORKTREE_BRANCH] $STATE_MESSAGE" \
        -sound default
    fi
    ;;
esac
