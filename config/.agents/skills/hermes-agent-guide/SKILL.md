---
name: hermes-agent-guide
description: |
  Hermes Agent（Nous Research の AI CLI エージェント）のセットアップ、設定、機能実装、トラブルシューティングの完全ガイド。
  ユーザーが hermes / hermes agent / ハーメス に言及したとき、config.yaml / .env / SOUL.md / MEMORY.md を編集するとき、gateway / hermes doctor / hermes config / hermes model / hermes tools / hermes profile / hermes cron / hermes plugins / hermes acp / hermes dashboard / hermes mcp について質問したとき、MCP サーバー追加・スキル管理（hermes skills）・ボイスモード / TTS / STT・cron タスク・Telegram / Discord / Slack / WhatsApp / Signal / Matrix / Mattermost / Email / SMS / WeCom / Feishu / QQBot 等のメッセージング Bot 構築・LLM プロバイダー切替・Bedrock / OpenRouter / Codex OAuth / Gemini OAuth・プラグイン開発・Shell hook・/steer / TUI / プロファイル管理に関する作業のときに使う。
  MCP や gateway が Hermes Agent 以外の文脈で使われているときや、関係ない話題のときは使わない。
---

# Hermes Agent 操作・実装ガイド

> **最終更新日**: 2026-04-24（Hermes Agent v0.11.0 / タグ `v2026.4.23` 時点）
> **参照元**: https://hermes-agent.nousresearch.com/docs / https://github.com/NousResearch/hermes-agent

Hermes Agent は Nous Research が開発した MIT ライセンスの AI CLI エージェント。ターミナル操作・Web 検索・ファイル編集・コード実行・メモリ・スキル・MCP 統合・17 メッセージングプラットフォーム対応・ボイスモード・スケジュールタスクなどの機能を持つ。

このスキルは公式ドキュメントと GitHub リリースノートを一次情報として網羅したリファレンス集。**SKILL.md 本体は索引と判断指針に留め、詳細は `references/` 配下を参照する**設計（プログレッシブディスクロージャー）。

## このスキルを使うときの行動原則

1. **まず索引（下表）で関連 reference を特定する**。SKILL.md 本体に詳細を書き写さない
2. **タスク別行動指針**（後述）に沿って、設定変更 / MCP 追加 / メッセージング構築 / トラブル対応の手順を選ぶ
3. **設定ファイル編集時は `~/.hermes/config.yaml` と `.env` を必ず先に読み**、現状を把握してから差分提案する
4. **コマンド出力（`hermes doctor`, `hermes status`, `hermes logs`）を診断の起点にする**

## reference 索引

| 知りたいこと | 参照先 |
|------------|--------|
| インストール / 初期セットアップ / Termux / Nix / 更新 | `references/getting-started.md` |
| `hermes <command>` のサブコマンド・スラッシュコマンド | `references/cli-commands.md` |
| `config.yaml` 全項目（カテゴリ別索引） | `references/configuration.md` → `references/config/<category>.md` |
| ツール・スキル・MCP・メモリ・ブラウザ・ボイス等の機能詳細 | `references/tools-and-features.md` → `references/features/<topic>.md` |
| TUI（Ink ベース v0.11.0）固有の操作 | `references/features/tui.md` |
| セッション管理・チェックポイント・ロールバック | `references/features/sessions.md` |
| プロファイル切替（業務 / 個人の分離など） | `references/features/profiles.md` |
| パーソナリティ / スキン | `references/features/personality-and-skins.md` |
| Web ダッシュボード + ダッシュボードプラグイン | `references/features/dashboard.md` |
| Transport ABC / AWS Bedrock ネイティブ / Responses API | `references/features/transports.md` |
| Cron・委譲・コード実行・フック・プラグイン・API サーバー・ACP・バッチ・RL | `references/automation-and-advanced.md` → `references/automation/<topic>.md` |
| Telegram / Discord / Slack / WhatsApp / Signal / Email / SMS / その他 13 プラットフォーム | `references/messaging-platforms.md` → `references/messaging/<platform>.md` |
| LLM プロバイダー（30+）の API キー名・設定 | `references/providers.md` |
| 環境変数の正確な一覧 | `references/environment-variables.md` |
| セキュリティモデル（7 層防御・承認・サンドボックス） | `references/security.md` |
| エラー解決・診断手順 | `references/troubleshooting.md` |
| 公式 docs `reference/` カテゴリへのインデックス | `references/reference-indexes.md` |

## タスク別行動指針

### 設定変更タスク
1. `~/.hermes/config.yaml` と `~/.hermes/.env` の現在内容を読む
2. 変更対象の設定項目を `references/configuration.md` 経由で該当ファイルから確認
3. 設定ファイルを編集し、変更内容と影響範囲をユーザーに説明
4. 必要に応じて `hermes doctor` または `hermes config check` で動作確認を案内

### MCP サーバー追加
1. `references/features/mcp.md` で stdio / HTTP の設定書式を確認
2. `config.yaml` の `mcp_servers:` に追記、`tools.include/exclude` でホワイトリスト
3. `mcp_servers.<name>.env` には**必要最小限の env だけ**渡す（プロセス全体の `.env` は見えない）
4. セッション内で `/reload-mcp`、または `hermes mcp test <name>` で接続確認

### メッセージングプラットフォーム構築
1. `references/messaging-platforms.md` から対象プラットフォームの個別 reference を開く
2. ボットトークン取得 → `.env` 設定 → `config.yaml` 設定 → `hermes gateway setup` の順で案内
3. アクセス制御（`*_ALLOWED_USERS` / `GATEWAY_ALLOWED_USERS` / DM ペアリング）を**必ず設定させる**
4. macOS / Linux 常駐は `hermes gateway install` → `hermes gateway start`

### プラグイン作成（v0.11.0 で大幅拡張）
1. `references/automation/plugins.md` を読む（`register_command`, `dispatch_tool`, `pre_tool_call` veto, `transform_tool_result` 等）
2. Python が不要な場合は `references/automation/hooks.md` の Shell hooks を選択
3. 配置先は `~/.hermes/plugins/<name>/`、`hermes plugins install <path>` で登録
4. ダッシュボードに UI を追加するなら `references/features/dashboard.md` のプラグイン API 節

### Cron / 自動化
1. `references/automation/cron.md` でスケジュール書式を確認
2. `hermes cron create` でインタラクティブ作成、または YAML を `~/.hermes/cron/<name>.yaml` に直接配置
3. コスト最適化が必要なら `wakeAgent` ゲート（事前スクリプト）と `enabled_toolsets` を活用
4. 結果送信先は `delivery.platform` で指定。送信不要な内部処理は `[SILENT]` プレフィックス

### トラブルシューティング
1. **最初に `hermes doctor`** を案内
2. `references/troubleshooting.md` でエラーパターンを照合
3. `hermes logs`, `hermes logs gateway -f`, `hermes logs errors -n 100` で詳細
4. `hermes dump` でサポート用設定ダンプ（API キーは自動マスク）

## クイックリファレンス（頻出コマンド）

```bash
# セッション
hermes                            # CLI 対話セッション
hermes --tui                      # 新型 Ink TUI（v0.11.0 推奨）
hermes chat -q "..."              # ワンショット
hermes -c                         # 最新セッション再開
hermes -r <id|タイトル>           # 特定セッション再開

# 設定・診断
hermes model                      # プロバイダー・モデル設定
hermes tools                      # ツール有効化設定
hermes config show / edit / set
hermes doctor / hermes status

# 拡張
hermes mcp add <name>             # MCP サーバー追加
hermes skills install <ref>       # スキルインストール
hermes plugins install <path>     # プラグインインストール

# Gateway / Cron
hermes gateway setup / start / status
hermes cron create / list / run
```

セッション内スラッシュコマンドは `references/cli-commands.md` の「スラッシュコマンド」節を参照。`/steer <prompt>`（v0.11.0 新規、実行中エージェントへの注入）など重要コマンドが追加されている。

## v0.11.0（2026-04-23）で押さえるべき変更

このスキル全体に v0.11.0 対応を反映済み。特に以下は新機能で頻出のため要注意:

- **Ink ベース TUI** — `hermes --tui` がフルリライト。詳細は `references/features/tui.md`
- **`/steer` コマンド** — 実行中のエージェントに mid-run nudge を注入
- **Transport ABC + AWS Bedrock ネイティブ** — `references/features/transports.md`
- **17 番目のプラットフォーム QQBot** — `references/messaging/other-platforms.md`
- **Plugin surface 大幅拡張** — `register_command` / `dispatch_tool` / `pre_tool_call` veto / `transform_tool_result` / Shell hooks / image_gen バックエンド / dashboard tabs
- **Webhook direct-delivery** — エージェントを起こさず通知転送
- **Smarter delegation** — `orchestrator` ロール、`max_spawn_depth`、ファイル協調レイヤー
- **Cron `wakeAgent` ゲート / per-job `enabled_toolsets`** — コスト削減
- **Auxiliary models 専用 UI** — `hermes model` の補助モデル設定画面

## ファイル構成（参考）

```
~/.hermes/
├── config.yaml          # 設定
├── .env                 # API キー
├── auth.json            # OAuth 認証情報（Codex / Gemini / Nous Portal 等）
├── SOUL.md              # エージェント人格
├── memories/            # MEMORY.md, USER.md
├── skills/              # スキル
├── plugins/             # プラグイン
├── cron/                # スケジュールジョブ
├── personalities/       # カスタムパーソナリティ
├── skins/               # カスタムスキン
├── profiles/            # プロファイル別設定（default 以外）
├── checkpoints/         # シャドウ git リポジトリ
├── sessions/            # Gateway セッションキャッシュ
├── state.db             # SQLite + FTS5
├── images/              # `/paste` した画像
└── logs/                # ログ
```

## コンテキストファイル優先順位

| ファイル | スコープ | 優先 |
|---------|---------|-----|
| `.hermes.md` / `HERMES.md` | git root まで探索 | 最高 |
| `AGENTS.md` | CWD + サブディレクトリ再帰 | 2 |
| `CLAUDE.md` | CWD + サブディレクトリ | 3 |
| `.cursorrules` | CWD のみ | 4 |
| `SOUL.md` | `~/.hermes/SOUL.md`（グローバル） | 独立レイヤー |

## このスキル自体の更新方針

- v0.11.x のパッチリリースで CLI/設定が変わった場合のみ、該当 reference を直接更新
- メジャー機能追加（Transport, Provider, Platform 追加など）は `references/` 内に該当ファイルを足す
- SKILL.md 本体は索引・行動指針・最低限のクイックリファレンスに留め、肥大化させない
