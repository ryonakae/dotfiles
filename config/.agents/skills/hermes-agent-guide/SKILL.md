---
name: hermes-agent-guide
description: |
  Hermes Agent（Nous Research の AI CLI エージェント）のセットアップ、設定、機能実装、トラブルシューティングの完全ガイド。
  ユーザーが hermes / hermes agent / ハーメス に言及したとき、config.yaml / .env / SOUL.md / MEMORY.md を編集するとき、gateway / hermes doctor / hermes config / hermes model / hermes tools について質問したとき、MCP サーバー追加・スキル管理（hermes skills）・ボイスモード / TTS・cron タスク・Telegram / Discord / Slack ボット構築・LLM プロバイダー切替に関する作業のときに使う。
  MCP や gateway が Hermes Agent 以外の文脈で使われているときや、関係ない話題のときは使わない。
---

# Hermes Agent 操作・実装ガイド

> 参照元: https://hermes-agent.nousresearch.com/docs / https://github.com/NousResearch/hermes-agent

Hermes Agent は Nous Research が開発した MIT ライセンスの AI CLI エージェント。ターミナル操作、Web 検索、ファイル編集、コード実行、メモリ、スキル、MCP 統合、17+ メッセージングプラットフォーム対応、ボイスモード、スケジュールタスクなどの機能を持つ。

## アーキテクチャ概要

```
hermes-agent/
├── run_agent.py              # AIAgent コア (~10,700行)
├── cli.py                    # CLI/TUI (~10,000行)
├── model_tools.py            # ツールディスパッチ（47ツール / 19ツールセット）
├── agent/                    # プロンプト構築・圧縮・キャッシュ・プロバイダー解決
├── tools/                    # ツール実装
├── gateway/                  # 18 プラットフォームアダプター
├── acp_adapter/              # IDE 統合
└── tests/                    # 3,000+ pytest テスト
```

エントリポイント: CLI → `AIAgent` ← Gateway / ACP
データフロー: ユーザー入力 → プロンプト構築 → API 呼出 → ツール実行 → セッション永続化

## インストール

```bash
# ワンラインインストーラー（Linux / macOS / WSL2 / Termux）
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc  # or source ~/.zshrc

# 初回セットアップ
hermes model       # LLM プロバイダー選択
hermes tools       # ツール有効化
hermes setup       # 全体セットアップ
```

**前提条件**: Git のみ。インストーラーが uv, Python 3.11, Node.js, ripgrep, ffmpeg を自動インストール。

## 設定ファイル

```
~/.hermes/
├── config.yaml      # 設定（モデル、ターミナル、TTS 等）
├── .env             # API キー
├── SOUL.md          # エージェント人格
├── memories/        # MEMORY.md, USER.md
├── skills/          # スキル
├── state.db         # セッション DB (SQLite + FTS5)
└── logs/            # ログ
```

設定優先順位: CLI 引数 > config.yaml > .env > デフォルト

### リファレンスの使い分け

タスクに応じて適切な reference を読む。SKILL.md 本体で解決できない場合にのみ参照する。

| タスク | 参照先 |
|--------|--------|
| hermes コマンドの引数・サブコマンド確認 | `references/cli-commands.md` |
| config.yaml の設定項目・書式確認 | `references/configuration.md`（索引）→ `references/config/<category>.md` |
| ツール・機能の詳細動作 | `references/tools-and-features.md`（索引）→ `references/features/<topic>.md` |
| LLM プロバイダーの API キー名・設定方法 | `references/providers.md` |
| エラー解決・診断手順 | `references/troubleshooting.md` |
| Telegram/Discord/Slack 等のボット構築手順 | `references/messaging-platforms.md`（索引）→ `references/messaging/<platform>.md` |
| Cron, 委譲, コード実行, フック, プラグイン, API サーバー, バッチ, RL | `references/automation-and-advanced.md`（索引）→ `references/automation/<topic>.md` |
| 環境変数名の正確な一覧 | `references/environment-variables.md` |

## タスク別の行動指針

このスキルを参照するモデルは、以下のパターンに従って行動する。

### 設定変更タスク
1. まず `~/.hermes/config.yaml` と `~/.hermes/.env` の現在内容を読む
2. 変更対象の設定項目を SKILL.md 内の設定例か `references/configuration.md` で確認
3. 設定ファイルを編集し、変更内容をユーザーに説明する
4. 必要に応じて `hermes doctor` で動作確認を案内する

### MCP サーバー追加
1. `references/tools-and-features.md` の MCP セクションで設定書式を確認
2. config.yaml の `mcp_servers:` に新しいサーバーを追記
3. stdio（`command` + `args`）か HTTP（`url` + `headers`）かを判断
4. 必要に応じて `tools.include` でホワイトリストを設定
5. `/reload-mcp` の実行を案内

### メッセージングプラットフォーム構築
1. `references/messaging-platforms.md` で対象プラットフォームのセットアップ手順を確認
2. ボットトークン取得 → `.env` 設定 → `config.yaml` 設定の順で案内
3. `hermes gateway setup` の使用を推奨
4. アクセス制御（`*_ALLOWED_USERS` / DM ペアリング）を必ず設定させる

### トラブルシューティング
1. `hermes doctor` の実行を最初に案内
2. `references/troubleshooting.md` でエラーパターンを照合
3. `hermes logs` / `hermes dump` でログ・設定ダンプを確認
4. 解決策を具体的なコマンドや設定変更として提示

## 基本操作

```bash
hermes                    # 対話セッション開始
hermes --tui              # TUI モード（推奨）
hermes chat -q "..."      # ワンショット
hermes -c                 # 最新セッション再開
hermes -r <id>            # 特定セッション再開

hermes model              # プロバイダー・モデル設定
hermes config set KEY VAL # 設定変更
hermes doctor             # 診断
hermes update             # 最新版更新
```

## config.yaml の主要設定

```yaml
# モデル
model:
  default: "anthropic/claude-sonnet-4"
  provider: "openrouter"

# ターミナル（6種: local/docker/ssh/modal/daytona/singularity）
terminal:
  backend: local
  timeout: 180

# エージェント動作
agent:
  max_turns: 90
  reasoning_effort: ""    # none/minimal/low/medium/high/xhigh

# メモリ
memory:
  memory_enabled: true
  memory_char_limit: 2200

# コンテキスト圧縮
compression:
  enabled: true
  threshold: 0.50

# 表示
display:
  tool_progress: all      # off/new/all/verbose
  streaming: false

# TTS
tts:
  provider: "edge"        # edge/elevenlabs/openai/neutts/minimax/mistral/gemini/xai

# MCP サーバー
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue]

# セキュリティ
approvals:
  mode: manual            # manual/smart/off
```

## プロバイダー設定

30+ プロバイダー対応。最低 64,000 トークンコンテキスト必要。

主要プロバイダー:
- **OpenRouter**: `OPENROUTER_API_KEY` — マルチプロバイダールーティング（推奨）
- **Anthropic**: `ANTHROPIC_API_KEY`
- **DeepSeek**: `DEEPSEEK_API_KEY`
- **Google Gemini**: OAuth via `hermes model`
- **Custom**: ローカル Ollama/vLLM/llama.cpp 等

```bash
hermes model    # 対話型選択
# セッション内: /model claude-sonnet-4
```

## ツールシステム

47 ツール / 19 ツールセット:

| カテゴリ | ツール例 |
|---------|---------|
| Web | `web_search`, `web_extract` |
| ターミナル | `terminal`, `process` |
| ファイル | `read_file`, `patch` |
| ブラウザ | `browser_navigate`, `browser_vision` |
| エージェント | `todo`, `clarify`, `execute_code`, `delegate_task` |
| メモリ | `memory`, `session_search` |
| スキル | `skills_list`, `skill_view`, `skill_manage` |

```bash
hermes tools                     # 対話型ツール設定
hermes chat -t "web,terminal"   # 特定ツールセットで起動
```

## MCP 統合

外部ツールサーバーへの接続。stdio（ローカル）と HTTP（リモート）対応。

```yaml
# config.yaml
mcp_servers:
  # stdio サーバー
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/project"]

  # HTTP サーバー
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"

  # フィルタリング
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    tools:
      include: [list_issues, create_issue]  # ホワイトリスト
      exclude: [delete_repo]                # ブラックリスト
      resources: false
      prompts: false
```

ツール名規則: `mcp_<server>_<tool>` (例: `mcp_github_create_issue`)

設定変更後はセッション内で `/reload-mcp` を実行。

## スキルシステム

`~/.hermes/skills/` にスキルを配置。プログレッシブディスクロージャーで効率的にロード。

```bash
# スキル操作
hermes skills browse                        # 閲覧
hermes skills search kubernetes             # 検索
hermes skills install openai/skills/k8s     # インストール
hermes skills install official/security/1password

# セッション内
/skills browse
/gif-search funny cats                      # スキルをスラッシュコマンドとして使用
hermes -s hermes-agent-dev,github-auth      # スキル事前読み込み
```

### SKILL.md フォーマット

```yaml
---
name: my-skill
description: スキルの説明
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [python]
    category: devops
    fallback_for_toolsets: [web]
    requires_toolsets: [terminal]
---
# スキル本文（手順・参照等）
```

## メッセージングゲートウェイ

17+ プラットフォーム対応のバックグラウンドプロセス。

```bash
hermes gateway setup       # プラットフォーム設定
hermes gateway             # フォアグラウンド実行
hermes gateway install     # サービスインストール
hermes gateway start/stop  # サービス制御
hermes gateway status      # ステータス確認
```

### アクセス制御

```bash
# .env に設定
TELEGRAM_ALLOWED_USERS=123456789
DISCORD_ALLOWED_USERS=111222333

# DM ペアリング
hermes pairing approve telegram ABC12DEF
```

## メモリシステム

- **MEMORY.md** (2,200文字): 環境・慣例・学習 — エージェント自動管理
- **USER.md** (1,375文字): ユーザー設定・スタイル
- セッション開始時にシステムプロンプトに注入
- `session_search` で過去セッション検索可能（SQLite FTS5）

## コンテキストファイル

| ファイル | 用途 | 優先順位 |
|---------|------|--------|
| `.hermes.md` / `HERMES.md` | プロジェクト指示 | 最高 |
| `AGENTS.md` | プロジェクト指示 | 2 |
| `CLAUDE.md` | Claude Code 互換 | 3 |
| `.cursorrules` | Cursor IDE 互換 | 4 |
| `SOUL.md` | エージェント人格（グローバル） | 独立 |

## ボイスモード

```bash
pip install "hermes-agent[voice]"    # CLI 音声モード
/voice on                            # 有効化
/voice tts                           # TTS 切替
```

- **CLI**: Ctrl+B で録音、自動無音検出
- **ゲートウェイ**: Telegram/Discord で音声返信
- **Discord VC**: ボイスチャネル参加・ライブ会話

## セキュリティ

7層防御: ユーザー認可 → 危険コマンド承認 → コンテナ分離 → MCP 認証フィルタ → コンテキストスキャン → セッション分離 → 入力サニタイゼーション

```yaml
approvals:
  mode: manual    # manual（デフォルト）| smart | off

security:
  redact_secrets: true
  tirith_enabled: true
```

## FAQ

**Q: コストは?**
Hermes 自体は無料 (MIT)。LLM API 使用料のみ。ローカルモデルは完全無料。

**Q: Windows で動く?**
ネイティブ非対応。WSL2 を使用。

**Q: 複数人で使える?**
ゲートウェイで複数ユーザー対応。許可リスト/DM ペアリングでアクセス制御。

**Q: データはどこに送られる?**
設定した LLM プロバイダーのみ。テレメトリ収集なし。ローカル保存。

**Q: オフライン/ローカルモデルで使える?**
可能。`hermes model` → Custom endpoint で Ollama 等を設定。
