---
name: use-hermes-agent
description: |
  Hermes Agent（Nous Research の AI CLI / TUI / Desktop エージェント）をセットアップ・設定・運用・トラブルシュートするためのスキル。
  ユーザーが hermes / hermes agent / ハーメス / Hermes Desktop を使うとき、config.yaml / .env / SOUL.md / MEMORY.md を編集するとき、gateway / doctor / config / model / tools / profile / cron / plugins / acp / dashboard / mcp / curator / kanban / proxy / send / audit / portal について質問したときに使う。
  MCP サーバー追加、hermes skills、curator、Kanban swarm、`/goal` `/subgoal` `/undo`、ボイスモード、TTS / STT、cron、メッセージング連携、LLM プロバイダー切替、OAuth、プラグイン開発、Shell hook、プロファイル管理、Bitwarden Secrets Manager に関する作業でも使う。
  MCP や gateway が Hermes Agent 以外の文脈で使われているときや、関係ない話題のときは使わない。
---

# Hermes Agent 操作・実装ガイド

> **最終更新日**: 2026-06-07（Hermes Agent v0.16.0 / タグ `v2026.6.5` 「The Surface Release」時点）
> **参照元**: https://hermes-agent.nousresearch.com/docs / https://github.com/NousResearch/hermes-agent

Hermes Agent は Nous Research が開発した MIT ライセンスの AI エージェント。CLI / TUI に加え、v0.16.0 から **macOS / Linux / Windows 向けネイティブ Desktop App** が登場。ターミナル操作・Web 検索・ファイル編集・コード実行・メモリ・スキル・MCP 統合・**23 メッセージングプラットフォーム対応**・ボイスモード・スケジュールタスク・**マルチエージェント Kanban**・**自律スキルキュレーター**などの機能を持つ。

このスキルは公式ドキュメントと GitHub リリースノートを一次情報として網羅したリファレンス集。**SKILL.md 本体は索引と判断指針に留め、詳細は `references/` 配下を参照する**設計（プログレッシブディスクロージャー）。

## このスキルを使うときの行動原則

1. **まず索引（下表）で関連 reference を特定する**。SKILL.md 本体に詳細を書き写さない
2. **タスク別行動指針**（後述）に沿って、設定変更 / MCP 追加 / メッセージング構築 / Kanban 構築 / トラブル対応の手順を選ぶ
3. **設定ファイル編集時は `~/.hermes/config.yaml` と `.env` を必ず先に読み**、現状を把握してから差分提案する
4. **コマンド出力（`hermes doctor`, `hermes status`, `hermes logs`, `hermes audit`）を診断の起点にする**

## reference 索引

| 知りたいこと | 参照先 |
|------------|--------|
| インストール / 初期セットアップ / pip / portal / Termux / Nix / 更新 | `references/getting-started.md` |
| `hermes <command>` のサブコマンド・スラッシュコマンド | `references/cli-commands.md` |
| `config.yaml` 全項目（カテゴリ別索引） | `references/configuration.md` → `references/config/<category>.md` |
| ツール・スキル・MCP・メモリ・ブラウザ・ボイス等の機能詳細 | `references/tools-and-features.md` → `references/features/<topic>.md` |
| **Hermes Desktop App（v0.16.0 新規）** | `references/features/desktop.md` |
| **マルチエージェント Kanban（v0.13.0 導入、v0.15.0 で本格化）** | `references/features/kanban.md` |
| **自律スキルキュレーター（v0.12.0 導入、curator）** | `references/features/curator.md` |
| **`/goal` / `/subgoal` / `/undo`（永続目標と取消）** | `references/features/goals.md` |
| TUI（Ink ベース）固有の操作 | `references/features/tui.md` |
| セッション管理・チェックポイント・ロールバック | `references/features/sessions.md` |
| プロファイル切替（業務 / 個人の分離、リモート gateway 接続） | `references/features/profiles.md` |
| パーソナリティ / スキン | `references/features/personality-and-skins.md` |
| Web ダッシュボード + ダッシュボードプラグイン + 完全管理パネル | `references/features/dashboard.md` |
| Transport ABC / AWS Bedrock ネイティブ / Responses API / Codex app-server | `references/features/transports.md` |
| Cron・委譲・コード実行・フック・プラグイン・API サーバー・ACP・バッチ・RL | `references/automation-and-advanced.md` → `references/automation/<topic>.md` |
| Telegram / Discord / Slack / WhatsApp / Signal / Email / SMS / Microsoft Teams / Google Chat / LINE / SimpleX / ntfy / Tencent 元宝 等 23 プラットフォーム | `references/messaging-platforms.md` → `references/messaging/<platform>.md` |
| LLM プロバイダー（30+）の API キー名・設定 | `references/providers.md` |
| 環境変数の正確な一覧 | `references/environment-variables.md` |
| セキュリティモデル（多層防御・承認・サンドボックス・mTLS MCP・Bitwarden Secrets Manager） | `references/security.md` |
| エラー解決・診断手順 | `references/troubleshooting.md` |
| 公式 docs `reference/` カテゴリへのインデックス | `references/reference-indexes.md` |

## タスク別行動指針

### 設定変更タスク
1. `~/.hermes/config.yaml` と `~/.hermes/.env` の現在内容を読む
2. 変更対象の設定項目を `references/configuration.md` 経由で該当ファイルから確認
3. 設定ファイルを編集し、変更内容と影響範囲をユーザーに説明
4. 必要に応じて `hermes doctor` または `hermes config check` で動作確認を案内

### MCP サーバー追加
1. `references/features/mcp.md` で stdio / HTTP / SSE / mTLS の設定書式を確認
2. **`hermes mcp` でカタログピッカーを起動**（v0.15.0 から Nous-approved catalog 提供）→ 選択 → 自動セットアップ、または `hermes mcp add <name>`
3. 手動設定の場合は `config.yaml` の `mcp_servers:` に追記、`tools.include/exclude` でホワイトリスト
4. `mcp_servers.<name>.env` には**必要最小限の env だけ**渡す（プロセス全体の `.env` は見えない）
5. セッション内で `/reload-mcp`、または `hermes mcp test <name>` で接続確認

### メッセージングプラットフォーム構築
1. `references/messaging-platforms.md` から対象プラットフォームの個別 reference を開く
2. ボットトークン取得 → `.env` 設定 → `config.yaml` 設定 → `hermes gateway setup` の順で案内
3. アクセス制御（`*_ALLOWED_USERS` / `GATEWAY_ALLOWED_USERS` / `allowed_channels` / `allowed_chats` / `allowed_rooms` / DM ペアリング）を**必ず設定させる**
4. macOS / Linux 常駐は `hermes gateway install` → `hermes gateway start`、クロスプロファイル状態は `hermes gateway list`

### Kanban / マルチエージェント実行
1. `references/features/kanban.md` を読む（durable board、heartbeat / reclaim、`max_in_progress`、claim TTL）
2. シンプルな並列実行は `hermes kanban swarm` で root + workers + verifier + synthesizer グラフを自動生成
3. `kanban.notification_sources` でクロスプロファイル通知配信
4. 失敗時は `hermes kanban list --sort` で stale-task / retry fingerprint を確認

### `/goal` / 永続目標タスク
1. セッション内で `/goal <description>` — クロスターン永続目標として登録（Ralph loop）
2. 進捗チェックポイントは `/subgoal <text>` で追加
3. 取消は `/undo [N]` で過去 N ターンまで戻る（v0.16.0）
4. 詳細は `references/features/goals.md`

### プラグイン作成
1. `references/automation/plugins.md` を読む（`register_command`, `dispatch_tool`, `pre_tool_call` veto, `transform_tool_result`, `transform_llm_output`, `pre_gateway_dispatch`, `pre/post_approval_request`, `ctx.llm`, `tool_override`, `register_tts_provider`, `register_transcription_provider`, `register_auxiliary_task` 等）
2. Python が不要な場合は `references/automation/hooks.md` の Shell hooks を選択
3. 配置先は `~/.hermes/plugins/<name>/`、`hermes plugins install <path>` で登録
4. ダッシュボードに UI を追加するなら `references/features/dashboard.md` のプラグイン API 節

### Cron / 自動化
1. `references/automation/cron.md` でスケジュール書式を確認
2. `hermes cron create` でインタラクティブ作成、または YAML を `~/.hermes/cron/<name>.yaml` に直接配置
3. コスト最適化は `wakeAgent` ゲート（事前スクリプト）、`enabled_toolsets`、**`no_agent` モード**（agent を起こさずスクリプト実行のみ、v0.13.0）を活用
4. per-job `workdir` / `context_from` / `profile` の指定可（v0.12.0+）
5. 結果送信先は `delivery.platform`。送信不要な内部処理は `[SILENT]` プレフィックス

### Hermes Desktop App セットアップ
1. `references/features/desktop.md` を読む
2. macOS/Linux/Windows native アプリ。in-app self-update 対応
3. リモート Hermes（自宅サーバー / hosted / チームメイト）へ OAuth or username/password で接続可能
4. 各プロファイルが独自リモートホストを持てる
5. concurrent multi-profile sessions、cross-profile `@session` リンク

### トラブルシューティング
1. **最初に `hermes doctor`** を案内
2. `references/troubleshooting.md` でエラーパターンを照合
3. `hermes logs`, `hermes logs gateway -f`, `hermes logs errors -n 100` で詳細
4. `hermes dump` でサポート用設定ダンプ（API キーは自動マスク）、`hermes debug share` でアップロード（redaction 通過）
5. supply-chain audit は `hermes audit`（OSV.dev、v0.15.0）

## クイックリファレンス（頻出コマンド）

```bash
# セッション
hermes                            # CLI 対話セッション（default_interface 設定で TUI も可）
hermes --tui                      # Ink TUI を明示起動
hermes --cli                      # CLI を明示起動（v0.16.0）
hermes chat -q "..."              # ワンショット
hermes -z "..."                   # 非対話 one-shot（v0.12.0、--model/--provider 対応）
hermes -c                         # 最新セッション再開
hermes -r <id|タイトル>           # 特定セッション再開

# 設定・診断
hermes model                      # プロバイダー・モデル設定（fuzzy picker, v0.16.0）
hermes tools                      # ツール有効化設定
hermes config show / edit / set
hermes doctor / hermes status
hermes audit                      # 依存関係の supply-chain audit（v0.15.0）
hermes prompt-size                # プロンプトサイズ診断（v0.16.0）

# 拡張
hermes mcp                        # MCP カタログピッカー（v0.15.0）
hermes mcp add <name>             # MCP サーバー追加
hermes skills install <ref>       # スキルインストール（HTTP(S) URL も可、v0.12.0）
hermes plugins install <path>     # プラグインインストール
hermes curator                    # 自律スキルキュレーター起動（v0.12.0）
hermes proxy                      # OpenAI 互換ローカルプロキシ（OAuth 経由、v0.14.0）

# Gateway / Cron / Kanban
hermes gateway setup / start / status / list
hermes cron create / list / run
hermes kanban list / promote / archive / swarm

# 認証 / 配信
hermes auth add <provider>        # OAuth/API キー登録（旧 hermes login）
hermes send <platform> <target>   # スクリプト出力を任意プラットフォームに pipe（v0.15.0）
hermes portal                     # Quick Setup via Nous Portal（v0.16.0）
```

セッション内スラッシュコマンドは `references/cli-commands.md` の「スラッシュコマンド」節を参照。

## v0.16.0（2026-06-05）までの主要変更（v0.11.0 → v0.16.0 差分）

このスキルは v0.16.0 (`v2026.6.5` 「The Surface Release」) 対応。v0.11.0 からの大きな進化は以下:

### v0.16.0 — The Surface Release（2026-06-05）
- **Hermes Desktop（Electron）** — macOS/Linux/Windows ネイティブアプリ。in-app self-update、Cmd+K palette、drag-and-drop、concurrent multi-profile sessions、Simplified Chinese 翻訳
- **リモート gateway へ OAuth / username-password でログイン可能** — Desktop / dashboard から自宅サーバー / hosted / チームメイトに接続
- **Web ダッシュボードが完全管理パネル化** — MCP catalog / Channels / credentials / webhooks / memory / gateway / hooks / System
- **`/undo [N]`** — 過去 N ターンを取り消し
- **デフォルトインターフェース選択** — `cli` / `tui` 切替（`--cli` flag）
- **`hermes portal`** — Quick Setup via Nous Portal
- **Fuzzy model picker** — desktop / web / TUI / CLI 全箇所、毎時カタログ更新
- **デフォルトスキル軽量化** — spotify（→ native plugin）/ linear（→ `hermes mcp install linear`）削除、`environments:` relevance gate 導入
- **CVE-2026-48710 (Starlette BadHost) パッチ済み**

### v0.15.x — The Velocity Release（2026-05-28）
- **Kanban が本格的なマルチエージェントプラットフォームに成熟** — `hermes kanban swarm`、orchestrator auto-decomposition、worktree per task、scheduled tasks、claim TTL、retry fingerprinting
- **`session_search` 書き直し** — 4,500× 高速、~20ms
- **Promptware 防御** — Brainworm 系攻撃に対する chokepoint 防御
- **Bitwarden Secrets Manager** — 1 つの bootstrap token で全クレデンシャル管理（`BWS_ACCESS_TOKEN` / `secrets.bitwarden.*`）
- **ntfy が 23 番目のメッセージングプラットフォーム**
- **Skill bundles** — `/<name>` で複数スキル同時ロード
- **TUI session orchestrator** — 1 TUI ウィンドウで複数ライブセッション
- **`hermes audit`** — OSV.dev による supply-chain audit
- **`hermes send`** — スクリプト出力を任意プラットフォームに pipe
- **`hermes migrate xai`** — 退役モデルからの一括移行
- **MCP TLS client certificate (mTLS) サポート**
- **Nous-approved MCP catalog + interactive picker**
- **`/exit --delete`**、`hermes mcp` のカタログピッカー
- **`hermes login` → `hermes auth add`** にリネーム

### v0.14.0 — The Foundation Release（2026-05-16）
- **xAI Grok SuperGrok OAuth** + **grok-4.3 を 1M context** に
- **`hermes proxy`** — OAuth provider（Claude Pro / ChatGPT Pro / SuperGrok）を OpenAI 互換エンドポイントとして公開し、Codex / Aider / Cline / Continue から利用可能
- **`x_search`** — first-class X (Twitter) 検索ツール
- **Microsoft Teams** + **LINE** + **SimpleX Chat** 追加（メッセージング 22 platform 達成）
- **`pip install hermes-agent`** で PyPI から起動可能に
- **Cross-session 1h Claude prompt cache**（Anthropic / OpenRouter / Nous Portal）
- **`browser_console` 180x 高速化**、コールドスタート ~19 秒短縮
- **LSP semantic diagnostics on every write** — `write_file`/`patch` 後に実 LSP 実行
- **Discord channel history backfill**（デフォルト ON）
- **Native Windows サポート（early beta）**
- **`/handoff`** — ライブセッション転送（モデル / persona / profile）
- **`/subgoal <text>`** で active `/goal` に criteria 追加

### v0.13.0 — The Tenacity Release（2026-05-07）
- **Durable Multi-Agent Kanban** — heartbeat / reclaim / zombie 検出
- **`/goal` (Ralph loop)** — 永続クロスターン目標
- **Checkpoints v2** — state persistence の書き直し
- **セキュリティ波**: 8 P0、redaction デフォルト ON、TOCTOU 修正、SSRF floor 強制、cron prompt-injection scan
- **Providers がプラグインに** — `ProviderProfile` ABC
- **`/handoff` / `/steer` / `/queue` の ACP 化**
- **Google Chat**（20 番目のプラットフォーム）
- **MCP SSE transport** + OAuth forwarding
- **7 ロケール対応**（zh/ja/de/es/fr/uk/tr）

### v0.12.0 — The Curator Release（2026-04-30）
- **Autonomous Curator** — `hermes curator` がスキルライブラリを自動メンテナンス（採点 / 統合 / 剪定）
- **自己改善ループ大幅強化** — class-first 採点、active-update バイアス
- **TUI コールドスタート ~57% 削減**
- **Microsoft Teams**（プラグイン経由）/ **Tencent 元宝（Yuanbao）** 追加
- **Spotify ネイティブ統合**（v0.16.0 で再び bundled skill から削除）
- **Vercel Sandbox バックエンド**（v0.15.0 で削除）
- **`hermes proxy` の原型**（後の v0.14.0 で正式公開）
- **`/provider` `/plan` 廃止**、`/btw`（`/background` エイリアス）、`/mouse`、`/reload-skills`、`/busy`
- **新フック**: `pre_gateway_dispatch`、`pre_approval_request`、`post_approval_response`
- **`auxiliary.curator`**、`redaction.enabled`（デフォルト false、v0.13.0 で ON に戻る）、`prompt_caching.cache_ttl`、`tts.providers.<name>`

## ファイル構成（参考）

```
~/.hermes/
├── config.yaml          # 設定
├── .env                 # API キー
├── auth.json            # OAuth 認証情報（Codex / Gemini / SuperGrok / Nous Portal 等）
├── SOUL.md              # エージェント人格
├── memories/            # MEMORY.md, USER.md
├── skills/              # スキル
├── plugins/             # プラグイン
├── cron/                # スケジュールジョブ
├── kanban/              # Kanban ボード状態（v0.13.0+）
├── personalities/       # カスタムパーソナリティ
├── skins/               # カスタムスキン
├── profiles/            # プロファイル別設定（default 以外）
├── checkpoints/         # シャドウ git リポジトリ（v0.13.0 で書き直し）
├── sessions/            # Gateway セッションキャッシュ
├── state.db             # SQLite + FTS5
├── images/              # `/paste` した画像
├── logs/                # ログ
│   ├── curator/         # キュレーター実行ログ・REPORT.md
│   └── desktop.log      # Desktop App ログ（v0.16.0）
└── bws_cache.json       # Bitwarden Secrets キャッシュ（v0.15.0）
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

- v0.16.x のパッチリリースで CLI/設定が変わった場合のみ、該当 reference を直接更新
- メジャー機能追加（Transport, Provider, Platform 追加など）は `references/` 内に該当ファイルを足す
- SKILL.md 本体は索引・行動指針・最低限のクイックリファレンスに留め、肥大化させない
