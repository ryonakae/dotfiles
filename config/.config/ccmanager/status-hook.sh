#!/bin/sh

# tmux変数を更新
tmux set -g @ccmanager-branch "$CCMANAGER_WORKTREE_BRANCH"
tmux set -g @ccmanager-state "$CCMANAGER_NEW_STATE"

# 通知が必要なステートでOSC 777を送信
case "$CCMANAGER_NEW_STATE" in
  waiting_input)
    printf '\033]777;notify;Claude Code;[%s] Waiting for your input\007' "$CCMANAGER_WORKTREE_BRANCH" > /dev/tty
    ;;
  pending_auto_approval)
    printf '\033]777;notify;Claude Code;[%s] Pending auto approval\007' "$CCMANAGER_WORKTREE_BRANCH" > /dev/tty
    ;;
esac
