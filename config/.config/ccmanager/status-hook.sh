#!/bin/sh

# tmux変数を更新
if [ -n "$TMUX" ]; then
  tmux set -g @ccmanager-branch "$CCMANAGER_WORKTREE_BRANCH"
  tmux set -g @ccmanager-state "$CCMANAGER_NEW_STATE"
fi

# 通知が必要なステートでOSC 777を送信
case "$CCMANAGER_NEW_STATE" in
  waiting_input|pending_auto_approval)
    CCM_PID=$(ps -eo pid,command | grep '[n]ode.*ccmanager' | awk '{print $1}' | head -1)
    if [ -n "$CCM_PID" ]; then
      CCM_TTY=$(ps -o tty= -p "$CCM_PID" | tr -d ' ')
      if [ -n "$CCM_TTY" ] && [ "$CCM_TTY" != "??" ]; then
        printf '\033]777;notify;Claude Code;[%s] %s\007' \
          "$CCMANAGER_WORKTREE_BRANCH" "$CCMANAGER_NEW_STATE" > "/dev/$CCM_TTY" 2>/dev/null
      fi
    fi
    ;;
esac
