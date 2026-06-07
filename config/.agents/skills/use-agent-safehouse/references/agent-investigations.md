# エージェント別セキュリティ分析 詳細リファレンス

Agent Safehouse がテスト・分析した全13エージェントの詳細セキュリティレポート。

## 目次

1. [Claude Code](#claude-code)
2. [Codex](#codex)
3. [Gemini CLI](#gemini-cli)
4. [Cursor Agent](#cursor-agent)
5. [Copilot CLI](#copilot-cli)
6. [Aider](#aider)
7. [Goose](#goose)
8. [Cline](#cline)
9. [Kilo Code](#kilo-code)
10. [OpenCode](#opencode)
11. [Auggie](#auggie)
12. [Droid](#droid)
13. [Pi](#pi)

---

## Claude Code

**種別**: Anthropic の公式 CLI/TUI（コンパイル済み Node.js バイナリ）

### 認証・認証情報
- API キーは macOS Keychain に保存（v0.2.30〜）
- OAuth トークン管理（プロアクティブリフレッシュ、v1.0.110〜）
- 対応プロバイダー: Anthropic API, AWS Bedrock, Google Vertex AI, Microsoft Foundry

### ファイルシステム
- 設定: `~/.claude/`（階層的設定: ユーザー/プロジェクト/エンタープライズ）
- ユーザー: `~/.claude/settings.json`
- プロジェクト: `.claude/settings.json`
- エンタープライズ: `managed-settings.json`
- `CLAUDE.md` でプロジェクト指示（`@path/to/file.md` インポート構文）

### ネットワーク
- API: `api.anthropic.com`
- テレメトリ: Sentry.io, Statsig
- GitHub: `api.github.com`
- VS Code マーケットプレイス

### ツール
Bash, Read, Write, Edit, WebSearch, WebFetch, MCP ツール, カスタムスキル

### サンドボックス
- Bash サンドボックス（v2.0.24+）: Linux/Mac でネットワーク隔離（ドメイン許可リスト）
- **重要**: Read/Write/Edit ツールはサンドボックス対象外
- MCP ツールもサンドボックス外で動作
- バイナリはクローズドソースでソース監査不可

### 推奨対策
コンテナ + ネットワークファイアウォール、`allowManagedPermissionRulesOnly` の managed settings、Bash サンドボックスの厳格なネットワーク制御、`--dangerously-skip-permissions` の無効化

---

## Codex

**種別**: OpenAI の CLI（TypeScript ランチャー + Rust コア）

### アーキテクチャ
- TypeScript: 最小シム（`bin/codex.js`）→ Rust バイナリを spawn
- Rust: 60以上の crate（CLI, TUI, 認証, サンドボックス, MCP, 実行エンジン）

### 認証
- `OPENAI_API_KEY` / `CODEX_API_KEY` 環境変数
- ChatGPT ブラウザ OAuth
- 3つのバックエンド: ファイル（0600）、OS keyring、エフェメラル（メモリ内）
- macOS: Keychain（サービス名 "Codex Auth"）

### サンドボックスモデル（内蔵）
**設計**: メインプロセスは非サンドボックス。AI のツール呼び出しのみサンドボックス化。

| プラットフォーム | 方式 |
|-----------------|------|
| macOS | Apple Seatbelt（deny-by-default） |
| Linux | bubblewrap + Landlock + seccomp |
| Windows | Restricted process tokens |

- `.git/` と `.codex/` は書き込み可能ルート内でも自動的に読み取り専用
- プロセスハードニング: `ptrace(PT_DENY_ATTACH)`, `DYLD_*` 削除, コアダンプ無効化

### ファイルシステム
- 設定: `~/.codex/`（`CODEX_HOME` で上書き可能）
- `config.toml`, `auth.json`（0600）, `state_4.sqlite`, `sessions/`, `prompts/`, `skills/`
- プロジェクト: `.codex/config.toml`, `AGENTS.md`
- エンタープライズ: `/etc/codex/config.toml`, macOS MDM

### ネットワーク
- `api.openai.com`, `auth.openai.com`, `chatgpt.com`
- `localhost:1455`（OAuth コールバック）
- MITM ネットワークプロキシ（`codex-network-proxy`、`rama` ベース）

---

## Gemini CLI

**種別**: Google の CLI/TUI（TypeScript/Node.js v20+）

### 認証
- OAuth2, Gemini API キー, Vertex AI, Google Cloud ADC
- macOS Keychain（主）、AES-256-GCM 暗号化ファイル（フォールバック）

### 設定パス
- ユーザー: `~/.gemini/`（settings, memory, commands, skills）
- プロジェクト: `.gemini/`
- システム: `/Library/...`（macOS）, `/etc/`（Linux）

### サンドボックス（内蔵）
3つのオプション: macOS Seatbelt（デフォルト）、Docker、Podman

Seatbelt の6段階プロファイル: permissive-open（デフォルト）〜 restrictive-closed

### セーフティ制御
- 環境変数サニタイズ（認証情報パターンをブロック）
- Web fetch でプライベート IP をブロック
- ただしパターンマッチングベースのため、非標準名の認証情報はリークの可能性あり

---

## Cursor Agent

**種別**: プロプライエタリ AI コードエディタ（VS Code フォーク、Electron ベース）

### 実行モード
- ローカルエージェント: IDE 内で実行
- クラウドバックグラウンドエージェント: AWS Docker コンテナ

### セキュリティ上の懸念
- ローカルエージェントはユーザーファイルシステム全体の読み取りアクセスを持つ
- 書き込みはワークスペースディレクトリに限定

### 既知の CVE
- CVE-2026-22708: ターミナル許可リストのシェルビルトインによるバイパス
- CVE-2025-59944: 機密ファイル保護の大文字小文字感度バイパス
- CVE-2025-4609: Chromium サンドボックスエスケープの継承

### 推奨対策
ファイルシステム読み取りをワークスペースと明示的許可リストに制限、`.ssh/`・`.aws/`・`.env` へのアクセスをブロック、YOLO/auto-run モード禁止、`.cursor/mcp.json` の変更を保護

---

## Copilot CLI

**種別**: GitHub のターミナルネイティブ AI コーディングエージェント（npm 配布）

### セキュリティモデル
- **OS レベルサンドボックスなし**
- アドバイザリー権限システム（信頼ディレクトリ許可リスト、ツール別承認プロンプト）
- `--allow-all-tools`、`--dangerously-skip-permissions` フラグあり
- カーネル強制ではなく、CLI 自体のバグで迂回される可能性

### ファイルシステム
- `~/.copilot/`（設定・状態）
- `~/.config/gh/`（GitHub CLI 認証情報を読み取り）

### 認証
- macOS Keychain（主）、`~/.copilot/config.json`（フォールバック）
- 環境変数: `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`

---

## Aider

**種別**: Python ベース AI コーディングアシスタント（Apache 2.0、CLI）

### セキュリティ
- **内蔵サンドボックスなし**。全操作がユーザープロセスのフル権限で実行
- ランタイムで pip 経由の任意パッケージインストールが可能
- `shell=True` での `subprocess.Popen()` / `pexpect.spawn()`
- `--copy-paste` フラグで 0.5 秒間隔のクリップボードポーリング
- `.aiderignore` はアドバイザリーのみ、強制的な制限なし

### 推奨対策
コンテナ/VM 内での実行、または macOS Seatbelt / Linux seccomp での制限

---

## Goose

**種別**: Block の OSS AI コーディングエージェント（Rust）

### セキュリティ
- **内蔵サンドボックスなし**
- 制限なしのシェル実行（ユーザーのシェル bash をデフォルト使用）
- AppleScript による macOS フル自動化（`osascript`）
- `xcap` crate による画面キャプチャ

### 認証情報
- システム keyring（`keyring` crate 3.6.2）
- フォールバック: `~/.config/goose/secrets.yaml`（平文 YAML、`GOOSE_DISABLE_KEYRING` 時）

### 推奨対策
コンテナベース隔離、ネットワーク egress フィルタリング、AppleScript 無効化

---

## Cline

**種別**: VS Code 拡張 AI コーディングアシスタント

### セキュリティ
- **内蔵サンドボックスなし**
- `child_process.spawn()` で任意シェルコマンド実行
- VS Code: SecretStorage（macOS Keychain）、スタンドアロン: `~/.cline/data/secrets.json`（平文 JSON、暗号化なし）
- 20+ AI プロバイダー API に接続
- gRPC ProtoBus サーバー: insecure credentials でポート 26040
- 独自 Chromium ダウンロード（〜150MB、ポート 9222 でデバッグ有効化）
- `node-machine-id` でハードウェアシリアル番号読み取り

---

## Kilo Code

**種別**: VS Code 拡張（Cline/Roo Code フォーク）

### 特徴
- クラウドサービス、マルチエージェントオーケストレーション、音声入力、コードインデックス
- React 18, Vite, Tailwind CSS, Radix UI

### ファイルシステム
- 主ストレージ: `~/Library/Application Support/Code/User/globalStorage/kilocode.kilo-code/`
- グローバル設定: `~/.kilocode/`
- プロジェクト: `{workspace}/.kilocode/`
- Chromium キャッシュ、ベクトルストア（LanceDB）

### サブプロセス
Ripgrep, Git, FFmpeg, Chromium, MCP サーバー, agent-runtime 子プロセス

---

## OpenCode

**種別**: OSS AI コーディングエージェント（Go、CLI/TUI）

### セキュリティ
- **内蔵サンドボックスなし**
- 唯一のセーフティ: bash ツールで curl, wget, telnet, ブラウザを禁止するコマンドリスト

### ファイルシステム
- `.opencode/`（作業ディレクトリ相対）: SQLite DB, デバッグログ, カスタムコマンド

---

## Auggie

**種別**: Augment Computing のクローズドソース CLI（npm `@augmentcode/auggie`）

### セキュリティ
- 制限なしのシェル実行（`launch-process` ツール）
- クローズドソースのため独立したセキュリティ検証不可
- MCP ヘッダーの `${augmentToken}` トークン展開で認証情報リークの可能性

### 認証
- OAuth（v0.16.0+）: `auggie login`、`~/.augment/session.json`
- 環境変数: `AUGMENT_API_TOKEN`, `AUGMENT_SESSION_AUTH`

---

## Droid

**種別**: Factory AI のクローズドソース CLI（Bun ランタイム）

### 権限モデル（4段階）
- Default: 読み取り専用
- Auto Low: ファイル作成/編集、フォーマット
- Auto Medium: パッケージインストール、ローカル git commit
- Auto High: git push、デプロイスクリプト

### セキュリティ
- `--skip-permissions-unsafe` で全操作可能（使い捨てコンテナ専用）
- Droid Shield: シークレット・プロンプトインジェクション検出
- Shield Plus: Palo Alto Prisma AIRS による AI スキャン
- **内蔵コンテナ隔離なし**、"project directory only" はエージェントレベル制限

### 設定
- ユーザー: `~/.factory/settings.json`
- プロジェクト: `.factory/settings.json`
- Claude Code のエージェント定義（`~/.claude/agents/`）をインポート

---

## Pi

**種別**: TypeScript/Node.js コーディングエージェント CLI（モノレポ `pi-mono`）

### セキュリティ
- **デフォルトでサンドボックスなし**
- bash ツールがユーザーのフル権限で任意コマンド実行
- オプション: `@anthropic-ai/sandbox-runtime` によるサンドボックス拡張（明示的有効化が必要）

### 認証情報
- `~/.pi/agent/auth.json`（平文 JSON、パーミッション 0o600）
- セッション履歴: JSONL 形式

### ネットワーク
- LLM プロバイダー API、npm レジストリ、GitHub、OAuth エンドポイント
- OAuth 一時ローカルサーバー: ポート 51121, 8085, 1455

### 拡張機能リスク
拡張機能は任意のツール登録、プロセス spawn、ファイルシステムアクセス、ネットワークリクエストが可能。CLI フラグ、設定、プロジェクトディレクトリ、npm/git パッケージから読み込み。
