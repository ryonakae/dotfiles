---
allowed-tools: Bash(tmux:*)
description: Send a prompt to another tmux pane and focus on it
model: claude-haiku-4-5
---

tmux の別ペインにコマンドを送信し、そのペインへフォーカスする。「ペインで実行して」「tmuxで送信」などのリクエストで使用。

## 使い方

1. コマンドを入力状態にする（実行はしない）：
   `tmux send-keys -t <ペイン番号> '<コマンド>'`

2. 指定したペインにフォーカスを移動する：
   `tmux select-pane -t <ペイン番号>`

## 手順

1. `tmux list-panes` で対象のペイン番号を確認
2. `tmux send-keys -t <ペイン番号> '<コマンド>'`
3. `tmux select-pane -t <ペイン番号>` を実行