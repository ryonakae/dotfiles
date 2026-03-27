# Panes, Tabs, and Floating Panes

## 目次

- 使いどころ
- 画面モデル
- ペイン操作
- タブ操作
- フローティングペイン操作
- 状態確認
- CLI recipe
- 一次情報

## 使いどころ

このファイルは、人間向けショートカットではなく `zellij action` でペイン、タブ、フローティングペインを直接操作したいときに読む。

具体的なフラグはローカルのヘルプを優先する。

```bash
zellij action new-pane --help
zellij action new-tab --help
zellij action change-floating-pane-coordinates --help
```

## 画面モデル

- 1 セッションの中に複数タブがある。
- 1 タブの中に通常ペインとフローティングペインがある。
- フローティングペインは表示を消しても破棄されず、プロセスは継続できる。
- pane と tab は作成時に ID を返すことがあり、その ID を後続 action に渡して制御する。

## ペイン操作

主要 action:

| action | 用途 | よく使うオプション |
| --- | --- | --- |
| `new-pane` | 新しいペインを作る | `--name`, `--cwd`, `--floating`, `--stacked`, `--in-place`, `--close-on-exit` |
| `close-pane` | 対象ペインを閉じる | `--pane-id` |
| `rename-pane` | ペイン名を変える | `--pane-id` |
| `undo-rename-pane` | ペイン名を戻す | `--pane-id` |
| `move-focus` | 方向指定でフォーカス移動 | `left|right|up|down` |
| `move-pane` | ペイン配置を動かす | `left|right|up|down` |
| `move-pane-backwards` | 配置を逆順に回す | なし |
| `resize` | ペインをリサイズする | `increase|decrease` と border 方向 |
| `toggle-fullscreen` | fullscreen 切り替え | なし |
| `stack-panes` | 指定ペインを stack 化する | pane ID 群 |
| `toggle-pane-frames` | 枠表示を切り替える | なし |
| `set-pane-color` | pane の既定色を変える | `--pane-id` |
| `set-pane-borderless` / `toggle-pane-borderless` | 枠表示を制御する | `--pane-id` |

実務メモ:

- シェルを経由せずに直接コマンドを起動したいときは `new-pane -- <command>` を使う。
- ジョブ専用 pane には `--name` を付ける。
- レイアウト破壊を避けたいときは先に `list-panes --json --all` で geometry を確認する。

## タブ操作

主要 action:

| action | 用途 | よく使うオプション |
| --- | --- | --- |
| `new-tab` | 新しいタブを作る | `--name`, `--cwd`, `--layout` |
| `close-tab` | 現在タブを閉じる | なし |
| `close-tab-by-id` | ID 指定で閉じる | tab ID |
| `rename-tab` | 現在タブ名を変える | なし |
| `rename-tab-by-id` | ID 指定で名前変更する | tab ID |
| `undo-rename-tab` | タブ名を戻す | なし |
| `move-tab` | タブ順を左右に動かす | `left|right` |
| `go-to-tab` | 位置で移動する | index |
| `go-to-tab-by-id` | ID で移動する | tab ID |
| `go-to-tab-name` | 名前で移動する | `name` |
| `go-to-next-tab` / `go-to-previous-tab` | 前後移動する | なし |
| `switch-session` | 別セッションへ切り替える | `--layout`, `--pane-id`, `--tab-position` |

実務メモ:

- 新しい作業面を足すだけなら `new-tab --layout` を優先する。
- 今あるタブの再配置は `override-layout` を使い、タブ自体を増やすなら `new-tab` を使う。
- 現在アクティブなタブに強く依存する action を使う前に `current-tab-info --json` か `list-tabs --json --all` で対象を確認する。

## フローティングペイン操作

主要 action:

| action | 用途 | よく使うオプション |
| --- | --- | --- |
| `toggle-floating-panes` | フローティング面の表示を切り替える | なし |
| `show-floating-panes` | フローティング面を表示する | `--tab-id` |
| `hide-floating-panes` | フローティング面を非表示にする | `--tab-id` |
| `toggle-pane-embed-or-floating` | 埋め込みと floating を切り替える | `--pane-id` |
| `toggle-pane-pinned` | always-on-top を切り替える | `--pane-id` |
| `change-floating-pane-coordinates` | floating pane の位置とサイズを変える | `--pane-id`, `--x`, `--y`, `--width`, `--height`, `--pinned` |

覚えること:

- `show-floating-panes` と `hide-floating-panes` は終了コードでも状態を返す。
- floating pane のサイズや位置は固定値だけでなく `%` でも指定できる。
- 既存 pane を floating 化したいときは `toggle-pane-embed-or-floating` を使う。

## 状態確認

| action | 出力 | 使いどころ |
| --- | --- | --- |
| `list-panes --json --all` | pane 一覧、state、geometry、tab 情報 | 変更前の現況確認 |
| `list-tabs --json --all` | tab 一覧、state、layout 情報 | active tab や floating visibility の確認 |
| `current-tab-info --json` | 現在タブの詳細 | 局所判断 |
| `dump-layout` | 現在構造の KDL | 保存、比較、再利用 |

## CLI recipe

ジョブ用 pane を追加する:

```bash
SESSION="work"
PANE_ID=$(zellij --session "$SESSION" action new-pane --name "tests" -- cargo test)
zellij --session "$SESSION" action dump-screen --pane-id "$PANE_ID" --full
```

新しいタブを custom layout で足す:

```bash
zellij --session work action new-tab --name "logs" --layout /tmp/logs.kdl
```

既存 pane を floating 化してサイズを決める:

```bash
zellij --session work action toggle-pane-embed-or-floating --pane-id terminal_3
zellij --session work action change-floating-pane-coordinates \
  --pane-id terminal_3 \
  --x "10%" --y "10%" --width "80%" --height "60%" --pinned true
```

現在の構造を保存してから上書きする:

```bash
zellij --session work action dump-layout > /tmp/current-layout.kdl
zellij --session work action override-layout /tmp/next-layout.kdl
```

## 一次情報

- https://zellij.dev/documentation/cli-actions.html
- https://zellij.dev/documentation/programmatic-control.html
- https://zellij.dev/tutorials/basic-functionality/
