#!/bin/sh
branch=$(tmux show -gv @ccmanager-branch 2>/dev/null)
if [ -n "$branch" ] && pgrep -x ccmanager >/dev/null 2>&1; then
  state=$(tmux show -gv @ccmanager-state 2>/dev/null)
  if [ -n "$state" ]; then
    echo " $branch ($state)"
  else
    echo " $branch"
  fi
else
  cd "$1" && git rev-parse --abbrev-ref HEAD 2>/dev/null
fi
