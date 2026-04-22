# Hermes Agent CLI コマンドリファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/reference/cli-commands

## グローバルエントリポイント

```
hermes [global-options] <command> [subcommand/options]
```

### グローバルオプション

| オプション | 説明 |
|--------|-------------|
| `--version`, `-V` | バージョン表示 |
| `--profile <name>`, `-p <name>` | プロファイル選択 |
| `--resume <session>`, `-r <session>` | セッション再開（ID またはタイトル） |
| `--continue [name]`, `-c [name]` | 最新セッション再開 |
| `--worktree`, `-w` | 分離 git worktree で開始 |
| `--yolo` | 危険コマンド承認スキップ |
| `--tui` | TUI モード起動 |

## 主要コマンド一覧

| コマンド | 用途 |
|---------|---------|
| `hermes chat` | 対話型 / ワンショットチャット |
| `hermes model` | プロバイダー・モデル選択 |
| `hermes gateway` | メッセージングゲートウェイ管理 |
| `hermes setup` | セットアップウィザード |
| `hermes config` | 設定管理 |
| `hermes tools` | ツール有効化設定 |
| `hermes skills` | スキル管理 |
| `hermes doctor` | 診断 |
| `hermes status` | ステータス確認 |
| `hermes update` | 最新版更新 |
| `hermes dump` | サポート用設定ダンプ |
| `hermes logs` | ログ閲覧 |
| `hermes sessions` | セッション管理 |
| `hermes cron` | スケジュールタスク管理 |
| `hermes pairing` | ペアリングコード管理 |
| `hermes auth` | 認証情報管理 |
| `hermes memory` | メモリプロバイダー管理 |
| `hermes mcp` | MCP サーバー管理 |
| `hermes plugins` | プラグイン管理 |
| `hermes webhook` | Webhook 管理 |
| `hermes acp` | IDE 統合 ACP サーバー |
| `hermes dashboard` | Web ダッシュボード起動 |
| `hermes profile` | プロファイル管理 |
| `hermes backup` | バックアップ |
| `hermes import` | バックアップ復元 |
| `hermes insights` | 使用分析 |
| `hermes uninstall` | アンインストール |

## hermes chat

```bash
hermes chat [options]
```

| オプション | 説明 |
|--------|-------------|
| `-q`, `--query "..."` | ワンショットプロンプト |
| `-m`, `--model <model>` | モデル指定 |
| `-t`, `--toolsets <csv>` | ツールセット指定 |
| `--provider <provider>` | プロバイダー強制指定 |
| `-s`, `--skills <name>` | スキル事前読み込み |
| `-v`, `--verbose` | 詳細出力 |
| `-Q`, `--quiet` | プログラマティックモード |
| `--image <path>` | 画像添付 |
| `--worktree` | git worktree 分離 |
| `--checkpoints` | チェックポイント有効化 |
| `--max-turns <N>` | 最大ツール呼び出し回数（デフォルト: 90） |

## hermes gateway

| サブコマンド | 説明 |
|------------|-------------|
| `run` | フォアグラウンド実行 |
| `start` | サービス開始 |
| `stop` | サービス停止 |
| `restart` | サービス再起動 |
| `status` | ステータス確認 |
| `install` | systemd/launchd サービスインストール |
| `uninstall` | サービス削除 |
| `setup` | プラットフォーム設定ウィザード |

## hermes config

| サブコマンド | 説明 |
|------------|-------------|
| `show` | 現在の設定表示 |
| `edit` | エディタで config.yaml 編集 |
| `set <key> <value>` | 設定値セット |
| `path` | config.yaml パス表示 |
| `env-path` | .env パス表示 |
| `check` | 欠落設定チェック |
| `migrate` | 新オプション追加 |

## hermes skills

| サブコマンド | 説明 |
|------------|-------------|
| `browse` | スキルレジストリ閲覧 |
| `search` | スキル検索 |
| `install` | スキルインストール |
| `inspect` | スキルプレビュー |
| `list` | インストール済みスキル一覧 |
| `check` | 更新確認 |
| `update` | 更新適用 |
| `audit` | セキュリティ再スキャン |
| `uninstall` | スキル削除 |
| `publish` | スキル公開 |
| `config` | プラットフォーム別有効/無効 |

## hermes cron

| サブコマンド | 説明 |
|------------|-------------|
| `list` | ジョブ一覧 |
| `create` | ジョブ作成 |
| `edit` | ジョブ編集 |
| `pause` | 一時停止 |
| `resume` | 再開 |
| `run` | 即時実行 |
| `remove` | 削除 |
| `status` | スケジューラ状態 |
| `tick` | 一回実行 |

## hermes mcp

| サブコマンド | 説明 |
|------------|-------------|
| `serve` | Hermes を MCP サーバーとして実行 |
| `add <name>` | MCP サーバー追加 |
| `remove <name>` | MCP サーバー削除 |
| `list` | 設定済みサーバー一覧 |
| `test <name>` | 接続テスト |
| `configure <name>` | ツール選択設定 |

## hermes profile

| サブコマンド | 説明 |
|------------|-------------|
| `list` | プロファイル一覧 |
| `use <name>` | デフォルト設定 |
| `create <name>` | 新規作成（`--clone` / `--clone-all`） |
| `delete <name>` | 削除 |
| `show <name>` | 詳細表示 |
| `alias <name>` | ラッパースクリプト管理 |
| `rename <old> <new>` | 名前変更 |
| `export <name>` | エクスポート |
| `import <archive>` | インポート |

## スラッシュコマンド（セッション内）

### セッション管理

| コマンド | 説明 |
|---------|-------------|
| `/new` / `/reset` | 新規セッション開始（現在のセッションを終了） |
| `/title <name>` | 現在のセッションにタイトルを設定 |
| `/retry` | 最後のエージェント応答を再生成 |
| `/undo` | 最後のメッセージを取消 |
| `/rollback` | チェックポイント一覧表示 |
| `/rollback N` | スナップショット N に復元 |
| `/rollback diff N` | 復元前に差分プレビュー |
| `/rollback N file` | 特定ファイルのみ復元 |
| `/background <prompt>` | バックグラウンドセッションで実行 |
| `/compress` | コンテキスト圧縮を手動実行 |
| `/usage` | トークン使用状況とコスト表示 |

### 設定変更

| コマンド | 説明 |
|---------|-------------|
| `/model` | 現在のモデル表示。引数でモデル変更 |
| `/model <provider/model>` | モデルを指定に変更 |
| `/reasoning high` / `medium` / `low` / `off` | 推論レベル変更 |
| `/personality <name>` | パーソナリティ設定 |
| `/verbose` | ツール出力の詳細表示を切替 |
| `/yolo` | 危険コマンド承認スキップの切替 |

### ツール・スキル

| コマンド | 説明 |
|---------|-------------|
| `/tools` | 有効なツール一覧表示 |
| `/skills browse` | スキルハブ閲覧 |
| `/skills search <query>` | スキル検索 |
| `/skills install <name>` | スキルインストール |
| `/reload-mcp` | MCP サーバー再読み込み |
| `/browser connect` | ローカル Chrome に CDP 接続 |

### 情報表示

| コマンド | 説明 |
|---------|-------------|
| `/help` | ヘルプ・コマンド一覧表示 |
| `/status` | 現在のセッション状態 |
| `/sessions` | 過去のセッション一覧 |

### ボイス・メディア

| コマンド | 説明 |
|---------|-------------|
| `/voice on` / `/voice off` | ボイスモード有効化/無効化 |
| `/voice tts` | TTS プロバイダー切替 |
| `/paste` | クリップボードの画像を貼り付け |

### メッセージング専用コマンド

Gateway セッション（Telegram、Discord 等）でのみ利用可能。

| コマンド | 説明 |
|---------|-------------|
| `/send <platform> <target> <message>` | 指定プラットフォームにメッセージ送信 |
| `/broadcast <message>` | 全 home_channel に一斉送信 |
| `/notify <platform> <message>` | home_channel に通知送信 |
| `/image <prompt>` | 画像生成してチャットに投稿 |
| `/tts <text>` | テキストを音声に変換して送信 |

## キーバインド

| キー | アクション |
|-----|--------|
| `Enter` | メッセージ送信 |
| `Alt+Enter` / `Ctrl+J` | 改行 |
| `Ctrl+B` | ボイス録音開始/停止 |
| `Ctrl+C` | エージェント中断（2回で強制終了） |
| `Ctrl+D` | 終了 |
| `Ctrl+Z` | バックグラウンドサスペンド（Unix） |
| `Tab` | オートコンプリート |
