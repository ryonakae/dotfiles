#!/bin/bash

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)  # Convert to absolute path
SESSION=$(basename "$PROJECT_DIR")

# 既存セッションがあればアタッチ
tmux has-session -t $SESSION 2>/dev/null
if [ $? == 0 ]; then
    echo "Session '$SESSION' already exists. Attaching..."
    tmux -u attach -t $SESSION
    exit 0
fi

# Create new session
tmux -u new-session -d -s $SESSION -c $PROJECT_DIR

# Rename window
tmux rename-window -t $SESSION:0 'main'

# # Split panes
# # Right pane
# tmux split-window -h -t $SESSION:0 -c $PROJECT_DIR
# # Split right pane vertically
# tmux split-window -v -t $SESSION:0.1 -c $PROJECT_DIR

# # Layout:
# # +----------------+----------+
# # |                | 0.1      |
# # |                | (作業用)  |
# # |  0.0           +----------+
# # |  (作業用)       | 0.2      |
# # |                | (作業用)  |
# # +----------------+----------+

# ペイン番号を表示
# tmux set-option -t $SESSION pane-border-status top
# tmux set-option -t $SESSION pane-border-format " #{pane_index}: #{pane_current_command} "

# Attach
tmux select-pane -t $SESSION:0.0
tmux -u attach -t $SESSION
