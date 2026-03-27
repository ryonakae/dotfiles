# Zellij CLI Control

## 目次

- 使いどころ
- トップレベルコマンド
- 機械操作の基本ループ
- 主要 `action` 一覧
- 観測と同期
- レイアウト関連コマンド
- セッション管理コマンド
- 一次情報

## 使いどころ

`zellij` を外部プロセスや別シェルから操作するときに読む。特に次の用途で使う。

- バックグラウンドセッションを作ってジョブを走らせる
- 既存セッションのペインやタブを増減させる
- 特定ペインへコマンドや入力を注入する
- ペイン出力を JSON やプレーンテキストで監視する
- レイアウトを適用、ダンプ、切り替えする

## 最初に確認すること

このファイルの内容より、実行環境の `--help` を優先する。特にフラグ、戻り値、JSON 形式、終了コードはバージョン差分の影響を受けやすい。

```bash
zellij --version
zellij --help
zellij action --help
zellij action <subcommand> --help
```

実務ルール:

- 参照資料は判断の土台に使い、最終的なコマンド組み立てはローカルの `--help` で確定する。
- スクリプト化する前に、使う subcommand を単体で 1 回試す。

## トップレベルコマンド

共通事項:

- 別セッションを対象にするときは `zellij --session <name> ...` を使う。
- `--layout <name-or-path>` は新規セッション起動時にも、既存セッション内で新しいタブを追加するときにも使える。

| コマンド | 主用途 | 補足 |
| --- | --- | --- |
| `attach` | セッションへ接続する | `--create`, `--create-background`, `--force-run-commands`, `--forget` が重要 |
| `action` | 実行中セッションへ操作を送る | Zellij の制御面の中心 |
| `run` | 新しいペインでコマンドを直接実行する | `action new-pane -- <command>` の便利版 |
| `edit` | 新しいペインでエディタを開く | `scrollback_editor` または `EDITOR`/`VISUAL` を使う |
| `plugin` | プラグインペインを開く | `floating`, `in-place`, `configuration` を扱える |
| `pipe` | プラグインにデータを送る | 対象プラグインが未起動なら起動できる |
| `subscribe` | ペイン描画更新を購読する | `--format json` で機械処理向き |
| `watch` | 読み取り専用でセッションを見る | セッション名だけで使える |
| `list-sessions` | セッション一覧を取る | `--short`, `--no-formatting` が便利 |
| `kill-session` | 実行中セッションを終了する | まず停止したいときに使う |
| `delete-session` | 保存済みセッションを削除する | `--force` で実行中セッションも削除できる |
| `options` | 起動時オプションを CLI から上書きする | `default_layout`, `mouse_mode`, `web_sharing` など |
| `setup` | 既定設定やレイアウトをダンプする | `--dump-config`, `--dump-layout`, `--check` が重要 |
| `web` | Web クライアント用サーバーを管理する | `--start`, `--stop`, `--status`, トークン生成を扱える |
| `convert-config` / `convert-layout` / `convert-theme` | 旧形式の変換 | 移行用途 |

## 機械操作の基本ループ

最も壊れにくい流れは「セッションを作る -> ID を受け取る -> 入力する -> 観測する -> 後始末する」。

```bash
SESSION="ci-run"

# バックグラウンドセッションを作る
zellij attach --create-background "$SESSION"

# 新しいペインでコマンドを直接実行し、作成された pane ID を受け取る
PANE_ID=$(zellij --session "$SESSION" action new-pane --name "tests" -- cargo test)

# 出力を読む
zellij --session "$SESSION" action dump-screen --pane-id "$PANE_ID" --full

# 後始末する
zellij --session "$SESSION" action close-pane --pane-id "$PANE_ID"
```

判断基準:

- シェル展開やエイリアスに依存しないなら `new-pane -- <command>` か `run -- <command>` を使う。
- 対話シェルの履歴や環境を利用したいときだけ `paste` と `send-keys` を使う。
- 後続処理が対象ペインに依存するなら、返された `terminal_<id>` や `plugin_<id>` を保持する。

既存シェルへ入力注入が必要なときの例外:

```bash
zellij --session "$SESSION" action paste --pane-id "$PANE_ID" "echo ready"
zellij --session "$SESSION" action send-keys --pane-id "$PANE_ID" Enter
```

## 主要 `action` 一覧

`zellij action --help` には多数の subcommand がある。ここでは制御面の地図だけを持ち、ペイン/タブ/フローティングの詳細は `references/panes-tabs-and-floating.md` に寄せる。

| 分類 | 主な action | 補足 |
| --- | --- | --- |
| 状態取得 | `list-panes`, `list-tabs`, `current-tab-info`, `list-clients`, `query-tab-names`, `dump-screen`, `dump-layout` | `list-panes --json`, `list-tabs --json`, `current-tab-info --json` を優先する |
| ペイン/タブ/フローティング | `new-pane`, `new-tab`, `close-pane`, `close-tab`, `resize`, `toggle-pane-embed-or-floating`, `change-floating-pane-coordinates`, `override-layout` | 詳細は `references/panes-tabs-and-floating.md` を読む |
| 入力注入 | `paste`, `write`, `write-chars`, `send-keys` | `paste` は bracketed paste mode を使うので複数行入力に向く |
| 名前変更とセッション操作 | `rename-pane`, `undo-rename-pane`, `rename-tab`, `rename-tab-by-id`, `undo-rename-tab`, `rename-session`, `switch-session`, `save-session`, `detach` | `switch-session` は `--layout`, `--pane-id`, `--tab-position` を受ける |
| プラグイン | `launch-plugin`, `launch-or-focus-plugin`, `start-or-reload-plugin`, `pipe` | `launch-or-focus-plugin` は session-manager などの内蔵プラグイン起動にも便利 |
| 観測 | `subscribe` | 長時間監視や NDJSON 取得に向く |

よく使う細部:

- `list-panes --json --all` で pane ID, state, geometry, tab 情報をまとめて取る。
- `list-tabs --json --all` で tab ID, active state, floating visibility, swap layout 名を取る。
- `dump-screen --full --ansi` でフルスクロールバックと色を含めて保存できる。
- `new-pane`, `new-tab`, `edit`, `launch-plugin`, `launch-or-focus-plugin` は作成した ID を stdout に返す。
- 具体的な pane/tab/floating の使い分けは `references/panes-tabs-and-floating.md` を読む。

## 観測と同期

観測方法は大きく 2 つある。

| 方法 | 使いどころ | 主なオプション |
| --- | --- | --- |
| `action dump-screen` | 今の表示を一度だけ読みたい | `--pane-id`, `--full`, `--ansi`, `--path` |
| `subscribe` | 描画更新を継続監視したい | `--pane-id`, `--format json`, `--scrollback`, `--ansi` |

ブロッキング系フラグ:

- `new-pane --blocking`: コマンド終了後、ペインが閉じるまで待つ
- `new-pane --block-until-exit`: コマンド終了まで待つ
- `new-pane --block-until-exit-success`: 終了コード `0` まで待つ
- `new-pane --block-until-exit-failure`: 非 `0` まで待つ
- `new-tab` にも `--block-until-exit*` がある

例:

```bash
PANE_ID=$(zellij --session "$SESSION" action new-pane --name "build" -- cargo build)
zellij --session "$SESSION" subscribe --pane-id "$PANE_ID" --format json
```

## レイアウト関連コマンド

| 操作 | コマンド | 用途 |
| --- | --- | --- |
| 新規起動時にレイアウト適用 | `zellij --layout <name-or-path>` | `layout_dir` 内の名前または `.kdl` パスを使う |
| 既存セッションとは別に新規作成 | `zellij --new-session-with-layout <name-or-path>` | 既存セッション内にいても必ず新セッションを作る |
| 既存セッションへ新タブ追加 | `zellij --layout <name-or-path>` | 実行中セッションでは新しいタブ群を追加する |
| 単一タブを作る | `zellij action new-tab --layout <path>` | `--cwd`, `--name`, `--layout-dir` も使える |
| 現在タブの構造を置き換える | `zellij action override-layout <path>` | `--apply-only-to-active-tab`, `--retain-existing-*` がある |
| 現在構造をダンプする | `zellij action dump-layout` | KDL として保存して再利用できる |

実用ルール:

- 複雑な KDL を書く前に `zellij setup --dump-layout default` を出力して土台にする。
- 実行中タブの再配置は `override-layout`、新しい作業面を増やすなら `new-tab --layout` を使う。
- 既存ペインを保ちながら適用したいときだけ `override-layout --retain-existing-terminal-panes` や `--retain-existing-plugin-panes` を使う。

## セッション管理コマンド

| 操作 | コマンド | 補足 |
| --- | --- | --- |
| 接続または作成 | `zellij attach <name>` | `--create`, `--create-background` が重要 |
| 一覧取得 | `zellij list-sessions --short --no-formatting` | スクリプトから扱いやすい |
| 読み取り専用接続 | `zellij watch <name>` | 観察専用 |
| 実行中セッションを停止 | `zellij kill-session <name>` | セッションを kill する |
| 保存状態も削除 | `zellij delete-session <name>` | `--force` で停止も兼ねる |
| Web 共有サーバー管理 | `zellij web --status` など | 共有が必要なときだけ使う |

`attach` の覚えておくべきフラグ:

- `--create`: なければ作る
- `--create-background`: 端末へ attach せずバックグラウンド作成する
- `--force-run-commands`: resurrect 時にコマンドを即実行する
- `--forget`: 保存済みセッションを消してから接続する
- `--remember`: Web 接続向け再認証情報を保存する

## 一次情報

- https://zellij.dev/documentation/controlling-zellij-through-cli.html
- https://zellij.dev/documentation/programmatic-control.html
- https://zellij.dev/documentation/cli-actions.html
- https://zellij.dev/documentation/zellij-run.html
- https://zellij.dev/documentation/zellij-plugin.html
- https://zellij.dev/documentation/zellij-subscribe.html
