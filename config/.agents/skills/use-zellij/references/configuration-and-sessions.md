# Configuration and Sessions

## 目次

- 設定ファイルの場所
- 主要オプション
- 任意: 人間向け導線
- セッション復元
- Web 共有
- 一次情報

## 設定ファイルの場所

Zellij は `config.kdl` を次の優先順で探す。

1. `--config-dir`
2. `ZELLIJ_CONFIG_DIR`
3. `$HOME/.config/zellij`
4. OS 既定パス
5. `/etc/zellij`

公式 docs の quickstart:

```bash
mkdir ~/.config/zellij
zellij setup --dump-config > ~/.config/zellij/config.kdl
```

補助コマンド:

- `zellij --config /path/to/config.kdl`: 設定ファイルを直接指定する
- `ZELLIJ_CONFIG_FILE=/path/to/config.kdl`: 環境変数で指定する
- `zellij options --clean`: 既定配置の設定ファイルを読まず、出荷時デフォルトで起動する
- `zellij setup --check`: 実際に見ているディレクトリを確認する

## 主要オプション

### 起動と場所

| オプション | 意味 | エージェント視点の使いどころ |
| --- | --- | --- |
| `default_layout` | 起動時に使う layout 名 | カスタム layout を常用するか判断するとき |
| `layout_dir` | layout を探すフォルダ | 名前指定で layout を呼びたいとき |
| `default_shell` | 新しい pane の既定 shell | shell 差異が問題になるとき |
| `default_cwd` | 新しい pane の既定 cwd | リポジトリ固定で使いたいとき |
| `session_name` | 起動時セッション名 | 安定したセッション名を決めたいとき |
| `attach_to_session` | 同名セッションへ attach する | 使い回し前提にしたいとき |
| `on_force_close` | 終了シグナル時の挙動 | terminal を閉じたときに detach か quit かを決める |

### スクロールバックと復元

| オプション | 意味 | 注意点 |
| --- | --- | --- |
| `scrollback_editor` | scrollback や `edit` で使うエディタ | `EDITOR` / `VISUAL` を明示的に上書きしたいとき |
| `session_serialization` | セッションをディスクへ保存する | `true` で resurrection が有効になる |
| `pane_viewport_serialization` | 可視 viewport も保存する | `session_serialization` と併用する |
| `scrollback_lines_to_serialize` | 保存する scrollback 行数 | `0` で全量。大きいほど重い |
| `serialization_interval` | 保存間隔 | 短くすると復元性は上がるが負荷も上がる |
| `disable_session_metadata` | session metadata 書き込み無効化 | `true` にすると session-manager や一覧が壊れやすい |
| `post_command_discovery_hook` | 復元用コマンド検出後の補正 | wrapper 経由で実行しているときに使う |

### 周辺オプション

| オプション | 意味 | 実務メモ |
| --- | --- | --- |
| `pane_frames` | pane frame 表示 | コンパクトさと視認性のトレードオフ |
| `stacked_resize` | stack を考慮したリサイズ挙動 | stacked panes を多用するなら重要 |
| `copy_command` | 独自コピーコマンド | macOS なら `pbcopy` が代表例 |
| `copy_clipboard` | `system` / `primary` | Wayland/X11 で primary を使うとき |
| `copy_on_select` | 選択時に自動コピー | 誤コピーを避けたいなら `false` |

### 共有と補助

| オプション | 意味 | 実務メモ |
| --- | --- | --- |
| `web_server` | ローカル Web サーバー起動 | browser 共有が必要なときだけ有効化する |
| `web_sharing` | 新規セッションを共有するか | `on`, `off`, `disabled` がある |
| `web_server_ip` / `web_server_port` | 待受先 | 既定は `127.0.0.1:8082` |
| `web_server_cert` / `web_server_key` | HTTPS 用証明書 | localhost 以外で待ち受けるなら重要 |
| `mirror_session` | 複数接続で同じカーソルを共有するか | 共同操作時に見る |
| `show_startup_tips` | 起動時 tips | onboarding 向け |
| `show_release_notes` | 新版の release notes 表示 | 更新直後の導線になる |

## 任意: 人間向け導線

エージェント運用では通常 `attach`, `list-sessions`, `switch-session` を優先する。この節は、ユーザーが human-facing な起動導線を求めたときだけ参照する。

| 導線 | 使い方 | 役割 |
| --- | --- | --- |
| `welcome-screen` | `zellij -l welcome` | terminal 起動直後の入り口 |
| `session-manager` | session 管理プラグイン | 実行中 session 内から別 session を探す |

できること:

- 新規セッションを名前付きで作る
- 特定フォルダを選んで開始する
- layout を選んで開始する
- 実行中セッションへ attach する
- 終了済みセッションを resurrect する

運用上のコツ:

- terminal の起動コマンドを `zellij -l welcome` にすると、Zellij を session ハブとして使いやすい。
- 復元したい作業は、終了前に `session-manager` からわかりやすい名前へ変更しておく。
- `session-manager` を成立させるには metadata が必要なので、`disable_session_metadata true` は慎重に使う。

## セッション復元

`session_serialization` が有効なとき、Zellij は pane/tab 構成と各 pane の実行コマンドを保存し、後で復元できる。

知っておくこと:

- 復元時、コマンドは即再実行されず、まず `Press ENTER to run...` のような確認状態で再現される。
- 破壊的コマンドが勝手に走らないための安全策として設計されている。
- `attach --force-run-commands` を使うと復元直後にコマンドを走らせられる。
- viewport や scrollback まで残したいなら `pane_viewport_serialization` と `scrollback_lines_to_serialize` を追加する。

## Web 共有

Web クライアント関連は `zellij web` と設定オプションの両方で扱う。

CLI 側:

- `zellij web --start`
- `zellij web --stop`
- `zellij web --status`
- `zellij web --create-token`
- `zellij web --create-read-only-token`
- `zellij web --list-tokens`
- `zellij web --revoke-token <name>`

実務ルール:

- 共有が不要なら `web_server false`, `web_sharing "off"` を維持する。
- localhost 以外で待ち受けるなら certificate と key を必ず用意する。
- 監視専用なら read-only token を優先する。

## 一次情報

- https://zellij.dev/documentation/configuration.html
- https://zellij.dev/documentation/command-line-options.html
- https://zellij.dev/documentation/options.html
- https://zellij.dev/tutorials/session-management/
- https://zellij.dev/tutorials/web-client/
