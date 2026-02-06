#!/bin/sh
branch_icon=""
branch=$(tmux show -gv @ccmanager-branch 2>/dev/null)

if [ -n "$branch" ] && pgrep -x ccmanager >/dev/null 2>&1; then
  state=$(tmux show -gv @ccmanager-state 2>/dev/null)
  if [ -n "$state" ]; then
    echo "$branch_icon $branch ($state)"
  else
    echo "$branch_icon $branch"
  fi
else
  # ccmanagerが起動していない、またはtmux変数が空の場合
  git_branch=$(cd "$1" && git rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ -n "$git_branch" ]; then
    echo "$branch_icon $git_branch"
  fi
fi
