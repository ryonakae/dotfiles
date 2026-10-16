---
name: use-agent-safehouse
description: |
  Agent Safehouse（macOS 向け sandbox-exec ベースのエージェントサンドボックスツール）をセットアップ・設定・運用するためのスキル。ポリシー構築、デバッグ、カスタマイズに対応。
  ユーザーが agent-safehouse / safehouse コマンド / sandbox-exec ポリシーを使うとき、`Operation not permitted` や `deny(` を含むサンドボックス拒否エラーをデバッグするとき、`--enable` の選定や `--append-profile` でカスタム .sb オーバーレイを作成するとき、.safehouse ファイルや local-overrides.sb を編集するとき、エージェントのファイルシステムアクセスを macOS カーネルレベルで制限したいときに使う。一般的な Linux sandbox や Docker/VM の質問には使わない。
---

# Agent Safehouse ガイド

Agent Safehouse は macOS ネイティブの `sandbox-exec` を利用した、LLM コーディングエージェント向けサンドボックスツール。カーネルレベルで deny-first のファイルシステム制限を適用し、依存関係ゼロで動作する。

## トラブルシュート：症状別ルーティング

| 症状 | まず試すこと | 詳細の参照先 |
|------|-------------|-------------|
| `Operation not permitted` エラー | 起動引数と最終profileの順序を確認し、標準機能・残るdeny・不足grantを切り分ける | `references/debugging-and-testing.md` の「一次診断手順」 |
| どのパスが拒否されたか不明 | `/usr/bin/log stream` で deny ログをストリーム | `references/debugging-and-testing.md` |
| `--enable` で何を有効化すべきか不明 | `safehouse --help` で導入版のfeature名を確認 | [公式options](https://agent-safehouse.dev/docs/options.html) |
| カスタム `.sb` ポリシーの書き方 | パスマッチャー（literal/subpath/prefix/regex）を確認 | `references/policy-and-customization.md` |
| 特定エージェント固有の問題 | 本ファイルの「対応エージェント」表で内蔵サンドボックスの有無を確認 | `references/agent-investigations.md` |
| LLM でプロファイルを自動生成したい | 検出コマンドを実行し、プロファイル生成プロンプトに従う | `references/llm-profile-generator.md` |
| ポリシーの順序・優先度の問題 | ポリシーレイヤーの「後のルールが優先」原則を確認 | `references/policy-and-customization.md` |

## 設計哲学

- **deny-first**: デフォルトで全アクセスを拒否し、必要なものだけ明示的に許可する
- **実用的な被害軽減**: 絶対的な隔離ではなく、プロンプトインジェクションや誤操作時の被害範囲を最小化する
- このdotfiles環境は普段の開発の互換性を優先し、HOME RW、`wide-read`、全環境継承、既存の `process-control` と広域IPC許可を維持する。`allow default` や `/` のRWには変更しない
- ネットワーク経由のデータ流出、サンドボックスエスケープ、許可済みチャネルの悪用は防げない

## 隔離モデルの位置づけ

| 観点 | VM | コンテナ | Safehouse |
|------|-----|---------|-----------|
| 隔離境界 | ゲスト OS | プロセス namespace/cgroup | macOS Seatbelt ポリシー |
| カーネル分離 | あり | なし（ホスト共有） | なし（ホスト共有） |
| ファイルシステム | ゲストのみ | コンテナ FS | deny-first + 明示的 allow |
| オーバーヘッド | 高 | 低〜中 | 非常に低 |
| ワークフロー互換性 | 低 | 中 | 高 |

最強の保護には VM 内で Safehouse を併用するレイヤードアプローチを推奨。

## インストール

```bash
# Homebrew（推奨）
brew install eugene1g/safehouse/agent-safehouse

# スタンドアロン
curl -fsSL https://agent-safehouse.dev/install.sh | sh
# ~/.local/bin/safehouse にインストールされる
```

## 基本的な使い方

```bash
# カレントディレクトリで Claude を起動
safehouse claude --dangerously-skip-permissions

# 追加の書き込みディレクトリを許可
safehouse --add-dirs=/path/to/other claude

# 読み取り専用ディレクトリを追加
safehouse --add-dirs-ro=/path/to/readonly claude

# カスタムポリシーを追加適用
safehouse --append-profile=my-policy.sb claude

# workdir 設定ファイルを信頼
safehouse --trust-workdir-config claude

# ワーキングディレクトリを明示指定
safehouse --workdir=/path/to/project claude

# ポリシーを出力して確認
safehouse --stdout claude
safehouse --explain claude
```

## 環境変数の渡し方

```bash
# 全環境変数を透過（秘密情報も含まれるので注意）
safehouse --env claude

# ファイルから環境変数をソース
safehouse --env=.env claude

# 特定の変数のみ選択的に渡す
safehouse --env-pass=ANTHROPIC_API_KEY,OPENAI_API_KEY claude
```

この環境のwrapperは互換性のため `--env` で全環境を継承する。ファイルへの直接アクセス拒否とは別の境界なので、継承した秘密値をログや応答へ出さない。

## オプション一覧

| フラグ | 説明 |
|--------|------|
| `--add-dirs=PATHS` | 書き込み可能ディレクトリを追加 |
| `--add-dirs-ro=PATHS` | 読み取り専用ディレクトリを追加 |
| `--workdir=DIR` | ワーキングディレクトリを指定 |
| `--trust-workdir-config` | `<workdir>/.safehouse` 設定を読み込み |
| `--append-profile=PATH` | カスタム `.sb` ポリシーを追加（繰り返し指定可） |
| `--allow-profile-writes` | appendしたprofileファイルへの標準deny-writeを省く。別途書き込みgrantは必要 |
| `--allow-workdir-config-writes` | `<workdir>/.safehouse` への標準deny-writeを省く |
| `--env` | ホスト環境変数を全て透過 |
| `--env=FILE` | ファイルから環境変数をソース |
| `--env-pass=NAMES` | 指定変数のみ透過 |
| `--output=PATH` | ポリシーをファイルに出力（実行も行う） |
| `--stdout` | ポリシーをstdoutに出力し、commandは実行しない |
| `--explain` | workdir・grant・profile選択のサマリをstderrに表示。command指定時は実行もする |
| `--enable=FEATURE` | オプション機能を有効化 |

`--enable` のfeature名と依存featureは、`safehouse --help` と [公式options](https://agent-safehouse.dev/docs/options.html) で確認する。

## デフォルトのアクセス制御

### 許可されるもの（デフォルト）

- workdir への読み書き
- Git 関連メタデータ（worktree 含む）
- macOS/システム/ツールチェーンのランタイム読み取り
- コマンドラインツール（git, make, clang 等）の実行
- プロセス実行・fork
- ネットワークアクセス（デフォルトオープン）
- 一時ディレクトリ

### ブロックされるもの（デフォルト）

- `~/.ssh` 秘密鍵
- シェル初期化ファイル（`.bashrc`, `.zshrc` 等）
- ブラウザデータ（Cookie、履歴、ブックマーク）
- クリップボードアクセス
- ホストプロセス列挙
- Xcode 開発ルート（完全版）
- raw デバイスアクセス
- `$HOME` の再帰的読み取り

### オプトイン（明示的に有効化が必要）

ブラウザ自動化、クリップボード統合、クラウド認証情報、Docker ソケット、Xcode ルート、LLDB、Keychain アクセス、広範な HOME 読み取り

## Git Worktree サポート

workdir が Git worktree の場合、Safehouse は自動的に：
- 共有 Git メタデータへのアクセスを許可
- 他の worktree パスへの読み取り専用アクセスを付与

HOME 外の worktree を参照する場合は、既存の許可範囲を確認し、不足する読み取り範囲だけを `--add-dirs-ro` で指定する。

## デスクトップアプリケーション対応

自動的にアプリバンドルを認識（Claude Desktop、VS Code 等）：

```bash
safehouse -- /Applications/Claude.app/Contents/MacOS/Claude
```

Electron アプリには `--no-sandbox` フラグを維持してネストされたサンドボックスの初期化を防止。

## ポリシーとカスタマイズ

ポリシーは複数のレイヤーを順に組み立て、後のルールが優先する。予期しない動作はまず最終profileの順序を確認する。レイヤー一覧、パスマッチャー、拡張ポイント、`.safehouse`、ローカルオーバーライド、配布は `references/policy-and-customization.md` を参照する。

**この環境の原則**: 開発の互換性を優先し、OS重要領域への書き込み範囲を維持する。標準機能と最終profile順から原因を診断し、承認された最小変更を行う。広いgrantを一律に避けたり、拒否ログをそのままallowへ変換したりしない。

追加profileは `compatibility.sb` → `local-overrides.sb` の順。IPCの広域許可とSimulatorの `system-fsctl` は `compatibility.sb` にまとめる。すでに許可されたMach/network/signalの個別allowを重複追加しない。

対話wrapper・Hermes gateway・dashboardの3経路は `--allow-profile-writes` を指定する。Safehouse標準のappend profile書き込み保護を省く設定であり、書き込みgrantは追加せず、`.safehouse` の保護も解除しない。承認された変更は `config/` の正本へ行い、次回起動で反映する。現在のsandboxで拒否された場合は無断で外側へ回さない。

## 対応エージェント

13種類のエージェントがテスト済み。Safehouse 本体の設定で解決できない、エージェント固有のファイルアクセスパターンや認証情報管理の問題を調べるときだけ `references/agent-investigations.md` を参照する。

| エージェント | 種別 | 内蔵サンドボックス |
|-------------|------|-------------------|
| Claude Code | CLI/TUI (Node.js) | Bash のみ（Read/Write/Edit は対象外） |
| Codex | CLI (TypeScript+Rust) | あり（Seatbelt/bubblewrap/Landlock） |
| Gemini CLI | CLI/TUI (TypeScript) | あり（Seatbelt 6段階プロファイル） |
| Cursor Agent | IDE (Electron) | なし（アプリレベル制限のみ） |
| Copilot CLI | CLI (Node.js) | なし（アドバイザリー権限のみ） |
| Aider | CLI (Python) | なし |
| Goose | CLI (Rust) | なし |
| Cline | VS Code 拡張 | なし |
| Kilo Code | VS Code 拡張 | なし |
| OpenCode | CLI/TUI (Go) | なし（禁止コマンドリストのみ） |
| Auggie | CLI (Node.js) | なし |
| Droid | CLI (Bun) | なし（アプリレベル権限のみ） |
| Pi | CLI (TypeScript) | オプション（sandbox-runtime） |

## リファレンスファイル

詳細が必要な場合は以下を参照：

- `references/policy-and-customization.md` — ポリシーレイヤー、パスマッチャー、拡張ポイント、`.safehouse`・ローカルオーバーライド、配布
- `references/debugging-and-testing.md` — 一次診断手順、拒否ログの調査、テストフレームワーク、E2E テスト
- `references/agent-investigations.md` — 全13エージェントの詳細セキュリティ分析
- `references/llm-profile-generator.md` — LLM を使ったカスタムプロファイル生成ガイド

## 参考リソース

- [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime) — Anthropic の公式サンドボックス実装
- [neko-kai/claude-code-sandbox](https://github.com/neko-kai/claude-code-sandbox) — 制限的な読み取りポリシー実験
- [n8henrie/trace.sh](https://github.com/n8henrie/trace.sh) — deny-to-allow プロファイル自動生成
