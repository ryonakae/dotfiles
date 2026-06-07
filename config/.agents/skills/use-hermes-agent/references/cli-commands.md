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
| `--tui` | TUI モードを明示起動 |
| `--cli` | CLI モードを明示起動（`default_interface` 上書き、v0.16.0） |
| `-z, --oneshot <prompt>` | 非対話 one-shot（v0.12.0、`--model` / `--provider` / `HERMES_INFERENCE_MODEL` 対応） |
| `--no-skills` | 空 profile 作成（v0.13.0） |

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
| `hermes dashboard` | Web ダッシュボード起動（`--stop` / `--status` / `register`） |
| `hermes profile` | プロファイル管理 |
| `hermes backup` | バックアップ |
| `hermes import` | バックアップ復元 |
| `hermes insights` | 使用分析 |
| `hermes uninstall` | アンインストール |
| `hermes curator` | 自律スキルキュレーター（v0.12.0） |
| `hermes kanban` | マルチエージェント Kanban（v0.13.0+） |
| `hermes proxy` | OpenAI 互換ローカルプロキシ（OAuth provider 公開、v0.14.0） |
| `hermes send` | スクリプト出力を任意プラットフォームに pipe（v0.15.0） |
| `hermes audit` | OSV.dev による supply-chain audit（v0.15.0） |
| `hermes migrate` | 退役モデル一括移行（例: `hermes migrate xai`、v0.15.0） |
| `hermes fallback` | fallback provider 管理（v0.12.0） |
| `hermes portal` | Quick Setup via Nous Portal（v0.16.0） |
| `hermes prompt-size` | プロンプトサイズ診断（v0.16.0） |
| `hermes auth add <provider>` | OAuth/API キー登録（旧 `hermes login`、v0.15.0 でリネーム） |
| `hermes debug share` | サポート用ログアップロード（redaction 通過） |

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
| `list` | クロスプロファイル status 一覧（v0.13.0） |
| `install` | systemd/launchd サービスインストール |
| `uninstall` | サービス削除 |
| `setup` | プラットフォーム設定ウィザード |

環境変数 `HERMES_GATEWAY_NO_SUPERVISE=1` または `--no-supervise` で systemd/launchd supervision を無効化（v0.15.1）。

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
| `install <ref>` | スキルインストール（HTTP(S) URL も可、v0.12.0） |
| `inspect` | スキルプレビュー |
| `list` | インストール済みスキル一覧（enabled/disabled 状態表示、v0.12.0） |
| `check` | 更新確認 |
| `update` | 更新適用 |
| `audit` | セキュリティ再スキャン |
| `uninstall` | スキル削除 |
| `publish` | スキル公開 |
| `config` | プラットフォーム別有効/無効 |

trusted tap: `OpenAI/skills`, `anthropic/skills`, `huggingface/skills`（v0.14.0）, `NVIDIA/skills`（v0.16.0）。

## hermes curator（v0.12.0+）

スキルライブラリを自律メンテナンスする。詳細は `features/curator.md`。

| サブコマンド | 説明 |
|------------|-------------|
| `(default)` | gateway cron ticker 上で background 実行（デフォルト 7 日サイクル） |
| `run` | 同期実行（結果が即座に見える、v0.13.0） |
| `status` | usage 順にランク表示（most-used / least-used） |
| `archive` | スキルをアーカイブ（v0.13.0） |
| `prune` | bundled/hub 以外を剪定 |
| `list-archived` | アーカイブ済み一覧 |

`auxiliary.curator` で curator 用モデルを統一管理。bundled/hub スキルは保護される（v0.16.0 で built-in skill の prune にも対応可）。

## hermes kanban（v0.13.0+）

マルチエージェント Kanban platform。詳細は `features/kanban.md`。

| サブコマンド | 説明 |
|------------|-------------|
| `list [--sort]` | タスク一覧 |
| `swarm` | Swarm v1 グラフ作成（root + workers + verifier + synthesizer + blackboard、v0.15.0） |
| `promote [--ids]` | 手動 todo → ready（v0.15.0） |
| `archive [--rm]` | アーカイブ / hard-delete（v0.15.0） |

## hermes cron

| サブコマンド | 説明 |
|------------|-------------|
| `list` | ジョブ一覧 |
| `create` | ジョブ作成（インタラクティブウィザード） |
| `edit` | ジョブ編集 |
| `pause` | 一時停止 |
| `resume` | 再開 |
| `run` | 即時実行 |
| `remove` | 削除 |
| `status` | スケジューラ状態 |
| `tick` | スケジューラを 1 サイクルだけ手動実行 |

## hermes mcp

| サブコマンド | 説明 |
|------------|-------------|
| `(default)` | Nous-approved MCP カタログの interactive picker（v0.15.0） |
| `serve` | Hermes を MCP サーバーとして実行 |
| `add <name>` | MCP サーバー追加（v0.13.0 で chat 誤起動の修正） |
| `install <name>` | カタログから 1-click install（例: `hermes mcp install linear`） |
| `remove <name>` | MCP サーバー削除 |
| `list` | 設定済みサーバー一覧 |
| `test <name>` | 接続テスト |
| `configure <name>` | ツール選択設定 |

mTLS（HTTP/SSE MCP）、SSE transport（v0.13.0）、TLS client certificate（v0.15.0）に対応。

## hermes sessions

| サブコマンド | 説明 |
|------------|-------------|
| `list` | セッション一覧 |
| `show <id>` | セッション詳細 |
| `optimize` | FTS5 セグメント merge（v0.16.0） |
| `delete <id>` | 削除 |
| `fork <id>` | 分岐セッション作成 |

`session_search` は v0.15.0 で aux-LLM 不要・4,500× 高速化（~20ms）。

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
| `/new [name]` | 新規セッション開始（v0.13.0 で optional name 引数） |
| `/reset` | 現在のセッションを終了 |
| `/title <name>` | 現在のセッションにタイトルを設定 |
| `/retry` | 最後のエージェント応答を再生成 |
| `/undo [N]` | 過去 N ターンまで取消（v0.16.0 で N 指定対応） |
| `/rollback` | チェックポイント一覧表示 |
| `/rollback N` | スナップショット N に復元 |
| `/rollback diff N` | 復元前に差分プレビュー |
| `/rollback N file` | 特定ファイルのみ復元 |
| `/background <prompt>` | バックグラウンドセッションで実行 |
| `/btw <prompt>` | `/background` のエイリアス（v0.12.0） |
| `/compress` | コンテキスト圧縮を手動実行 |
| `/usage` | トークン使用状況とコスト表示 |
| `/save` | TUI スナップショット（v0.16.0） |
| `/exit [--delete]` | 終了時にセッション削除（v0.15.0） |
| `/handoff` | セッションをモデル/persona/profile/他のセッションに転送（v0.13.0） |
| `/sessions` | 過去セッション一覧（v0.14.0、TUI） |

### 設定変更

| コマンド | 説明 |
|---------|-------------|
| `/model` | 現在のモデル表示（fuzzy picker、grouped 表示、v0.16.0） |
| `/model <provider/model>` | モデルを指定に変更 |
| `/reasoning high` / `medium` / `low` / `off` | 推論レベル変更 |
| `/personality <name>` | パーソナリティ設定 |
| `/verbose` | ツール出力の詳細表示を切替 |
| `/yolo` | 危険コマンド承認スキップの切替（mid-session bypass、v0.15.1 で修正） |
| `/steer <prompt>` | 実行中エージェントに次ツール呼び出し後の note 注入。v0.13.0 で ACP 対応 |
| `/queue <prompt>` | 後続キューに追加（v0.13.0、ACP 経由） |
| `/busy` | input mode に "steer" 第三オプション追加（v0.12.0） |
| `/mouse` | ConPTY ファントムマウス注入トグル（v0.12.0） |
| `/update` | CLI/TUI から `hermes update`（v0.15.0） |
| `/reload` | `.env` hot-reload（v0.12.0） |

### ツール・スキル

| コマンド | 説明 |
|---------|-------------|
| `/tools` | 有効なツール一覧表示 |
| `/skills browse` | スキルハブ閲覧 |
| `/skills search <query>` | スキル検索 |
| `/skills install <name>` | スキルインストール |
| `/<skill-bundle>` | 複数スキルを同時ロード（skill bundles、v0.15.0） |
| `/reload-mcp` | MCP サーバー再読み込み |
| `/reload-skills` | スキル再読み込み（v0.12.0） |
| `/browser connect` | ローカル Chrome に CDP 接続 |

### マルチエージェント / 目標

| コマンド | 説明 |
|---------|-------------|
| `/goal <description>` | クロスターン永続目標を登録（Ralph loop、v0.13.0） |
| `/subgoal <text>` | active `/goal` に criteria 追加（v0.14.0） |
| `/kanban` | Kanban ボードを開く（v0.13.0） |
| `/agents` | delegation 開始時にダッシュボード誘導（v0.16.0） |

### 情報表示

| コマンド | 説明 |
|---------|-------------|
| `/help` | ヘルプ・コマンド一覧表示 |
| `/status` | 現在のセッション状態 |
| `/debug` | デバッグ情報（v0.16.0 で `desktop.log` 含む） |

### 廃止されたコマンド

- `/provider` — v0.12.0 で削除（`/model` に統合）
- `/plan` — v0.12.0 で削除

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
