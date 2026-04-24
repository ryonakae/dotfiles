---
name: agent-safehouse-guide
description: |
  Agent Safehouse（macOS 向け sandbox-exec ベースのエージェントサンドボックスツール）のセットアップ、設定、ポリシー構築、デバッグ、カスタマイズの完全ガイド。
  ユーザーが agent-safehouse / safehouse コマンド / sandbox-exec ポリシーに言及したとき、`Operation not permitted` や `deny(` を含むサンドボックス拒否エラーをデバッグするとき、`--enable` の選定や `--append-profile` でカスタム .sb オーバーレイを作成するとき、.safehouse ファイルや local-overrides.sb を編集するとき、エージェントのファイルシステムアクセスを macOS カーネルレベルで制限したいときに使う。一般的な Linux sandbox や Docker/VM の質問には使わない。
---

# Agent Safehouse ガイド

Agent Safehouse は macOS ネイティブの `sandbox-exec` を利用した、LLM コーディングエージェント向けサンドボックスツール。カーネルレベルで deny-first のファイルシステム制限を適用し、依存関係ゼロで動作する。

## トラブルシュート：症状別ルーティング

| 症状 | まず試すこと | 詳細の参照先 |
|------|-------------|-------------|
| `Operation not permitted` エラー | `safehouse --explain` で現在のグラントを確認 → `--add-dirs` / `--add-dirs-ro` で必要なパスを追加 | 本ファイルの「デバッグ」セクション |
| どのパスが拒否されたか不明 | `/usr/bin/log stream` で deny ログをストリーム | `references/debugging-and-testing.md` |
| `--enable` で何を有効化すべきか不明 | 本ファイルの「--enable で有効化できる機能」一覧を確認 | — |
| カスタム `.sb` ポリシーの書き方 | パスマッチャー（literal/subpath/prefix/regex）を確認 | `references/policy-and-customization.md` |
| 特定エージェント固有の問題 | 本ファイルの「対応エージェント」表で内蔵サンドボックスの有無を確認 | `references/agent-investigations.md` |
| LLM でプロファイルを自動生成したい | 検出コマンドを実行し、プロファイル生成プロンプトに従う | `references/llm-profile-generator.md` |
| ポリシーの順序・優先度の問題 | ポリシーレイヤーの「後のルールが優先」原則を確認 | `references/policy-and-customization.md` |

### 一次診断手順

問題発生時はこの順序で進める：

1. **`safehouse --explain <command>`** — workdir とグラント情報のサマリを確認
2. **`safehouse --stdout <command>`** — 生成されたポリシー全体を出力して内容を確認
3. **`/usr/bin/log stream`** — deny ログをリアルタイムで監視し、拒否されたパス・操作を特定

## 設計哲学

- **deny-first**: デフォルトで全アクセスを拒否し、必要なものだけ明示的に許可する
- **実用的な被害軽減**: 絶対的な隔離ではなく、プロンプトインジェクションや誤操作時の被害範囲を最小化する
- **各ポリシールールは「エージェントがこれを必要とするか？」で判断する**
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

シェル関数として `safeenv`（全環境透過）と `safekeys`（API キーのみ転送）を設定するのが推奨。

## オプション一覧

| フラグ | 説明 |
|--------|------|
| `--add-dirs=PATHS` | 書き込み可能ディレクトリを追加 |
| `--add-dirs-ro=PATHS` | 読み取り専用ディレクトリを追加 |
| `--workdir=DIR` | ワーキングディレクトリを指定 |
| `--trust-workdir-config` | `<workdir>/.safehouse` 設定を読み込み |
| `--append-profile=PATH` | カスタム `.sb` ポリシーを追加 |
| `--env` | ホスト環境変数を全て透過 |
| `--env=FILE` | ファイルから環境変数をソース |
| `--env-pass=NAMES` | 指定変数のみ透過 |
| `--output=PATH` | ポリシーをファイルに出力（実行も行う） |
| `--stdout` | ポリシーをstdoutに出力 |
| `--explain` | workdir とグラント情報のサマリを表示 |
| `--enable=FEATURE` | オプション機能を有効化 |

### --enable で有効化できる機能

`docker`, `kubectl`, `shell-startup`, `browser`, `process-control`, `lldb`, `vscode`, `xcode`, `wide-fs-read`, `keychain`, `1password`, `cloud-credentials`

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

## ワーキングディレクトリの設定ファイル

プロジェクトルートに `.safehouse` ファイルを配置：

```
add-dirs-ro=/path/to/shared/libs
add-dirs=/path/to/output
```

`--trust-workdir-config` フラグで読み込む。

## ローカルオーバーライド

マシン固有の例外を `~/.config/agent-safehouse/local-overrides.sb` に記述。

## Git Worktree サポート

workdir が Git worktree の場合、Safehouse は自動的に：
- 共有 Git メタデータへのアクセスを許可
- 他の worktree パスへの読み取り専用アクセスを付与

worktree を安定した親ディレクトリ配下で作成する場合は `--add-dirs-ro` で親を指定。

## デスクトップアプリケーション対応

自動的にアプリバンドルを認識（Claude Desktop、VS Code 等）：

```bash
safehouse -- /Applications/Claude.app/Contents/MacOS/Claude
```

Electron アプリには `--no-sandbox` フラグを維持してネストされたサンドボックスの初期化を防止。

## ポリシーアーキテクチャ

ポリシーは以下のレイヤーで組み立てられる（後のルールが優先）：

1. `00-base.sb` — デフォルト deny、ヘルパー関数、HOME 置換トークン
2. `10-system-runtime.sb` — macOS ランタイムバイナリ、一時ディレクトリ、IPC
3. `20-network.sb` — ネットワークポリシー
4. `30-toolchains/*.sb` — Apple, Node, Python, Go, Rust, Bun, Java, PHP, Perl, Ruby
5. `40-shared/*.sb` — クロスエージェント共有モジュール
6. `50-integrations-core/*.sb` — Git, SSH agent, worktree 等
7. `55-integrations-optional/*.sb` — `--enable` でオプトイン
8. `60-agents/*.sb` — コマンド名でエージェント別プロファイルを選択
9. `65-apps/*.sb` — アプリバンドル別プロファイル
10. 設定/環境変数/CLI グラント、追加プロファイル

**順序が重要**: 後のルールが優先。予期しない動作はまず順序を確認。

詳細は `references/policy-and-customization.md` を参照。

## デバッグ（サンドボックス拒否の調査）

`Operation not permitted` エラーが発生した場合の調査手順：

```bash
# ライブで拒否ログをストリーム
/usr/bin/log stream --style compact \
  --predicate 'eventMessage CONTAINS "Sandbox:" AND eventMessage CONTAINS "deny("'

# 特定 PID パターンでフィルタ
/usr/bin/log stream --style compact \
  --predicate 'eventMessage CONTAINS "Sandbox: 2.1.34(" AND eventMessage CONTAINS "deny("'

# カーネルレベルの拒否を監視
/usr/bin/log stream --style compact \
  --predicate '(processID == 0) AND (senderImagePath CONTAINS "/Sandbox")'
```

**重要**: `/usr/bin/log` のフルパスを使うこと（シェルの `log` エイリアスと区別するため）。

### 拒否ログからルールへの変換

| ログの操作 | sandbox ポリシールール |
|------------|----------------------|
| ファイル操作 | `(allow <operation> (literal "<path>"))` |
| sysctl | `(allow sysctl-read (sysctl-name "<name>"))` |
| mach-lookup | `(allow mach-lookup (global-name "<name>"))` |

### ノイズ除去

dtracehelper や Apple サービスのフォルスポジティブを除外。`DYLD_USE_DTRACE=0` で dtrace を抑制可能。

詳細は `references/debugging-and-testing.md` を参照。

## カスタマイズ

6つの拡張ポイント：

1. `--append-profile` で読み込むカスタム `.sb` オーバーレイに認証情報拒否を追加
2. `profiles/20-network.sb` でネットワーク動作を調整
3. `profiles/40-shared/` で共有クロスエージェントルールを変更
4. `profiles/60-agents/` にエージェントプロファイルを追加
5. `profiles/65-apps/` にデスクトップアプリプロファイルを追加
6. `profiles/30-toolchains/` にツールチェーンプロファイルを追加

**原則**: 最小権限と狭い path グラントを優先。広い `subpath` グラントは避ける。

## 配布

```bash
# dist/safehouse.sh — ランタイム＋ポリシーモジュールを埋め込んだ自己完結スクリプト
./scripts/generate-dist.sh
```

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

- `references/policy-and-customization.md` — ポリシーアーキテクチャ詳細、パスマッチャー、カスタマイズ、配布
- `references/debugging-and-testing.md` — デバッグ手法、テストフレームワーク、E2E テスト
- `references/agent-investigations.md` — 全13エージェントの詳細セキュリティ分析
- `references/llm-profile-generator.md` — LLM を使ったカスタムプロファイル生成ガイド

## 参考リソース

- [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime) — Anthropic の公式サンドボックス実装
- [neko-kai/claude-code-sandbox](https://github.com/neko-kai/claude-code-sandbox) — 制限的な読み取りポリシー実験
- [n8henrie/trace.sh](https://github.com/n8henrie/trace.sh) — deny-to-allow プロファイル自動生成
