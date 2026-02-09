#!/bin/sh

# プロセスツリーを辿り、最初に見つかったmacOSアプリのBundle Identifierを返す
find_app_from_pid() {
  pid="$1"
  while [ "$pid" -gt 1 ] 2>/dev/null; do
    exe=$(ps -o comm= -p "$pid" 2>/dev/null)
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
  find_app_from_pid $PPID && return

  # tmux経由の場合はサーバーがデーモン化しておりプロセスツリーが切れるため、クライアントPIDから辿る
  if [ -n "$TMUX" ]; then
    client_pid=$(tmux display-message -p '#{client_pid}' 2>/dev/null)
    if [ -n "$client_pid" ]; then
      find_app_from_pid "$client_pid" && return
    fi
  fi

}

ACTIVATE_APP=$(detect_terminal_app)

case "$CCMANAGER_NEW_STATE" in
  waiting_input|pending_auto_approval)
    if [ -n "$ACTIVATE_APP" ]; then
      terminal-notifier \
        -title "CCManager" \
        -message "[$CCMANAGER_WORKTREE_BRANCH] $CCMANAGER_NEW_STATE" \
        -sound default \
        -activate "$ACTIVATE_APP"
    else
      terminal-notifier \
        -title "CCManager" \
        -message "[$CCMANAGER_WORKTREE_BRANCH] $CCMANAGER_NEW_STATE" \
        -sound default
    fi
    ;;
esac
