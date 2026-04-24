# デバッグとテスト 詳細リファレンス

## サンドボックス拒否のデバッグ

### 基本コマンド

`/usr/bin/log`（シェルの `log` エイリアスではなくフルパス）を使用：

```bash
# ライブで拒否ログをストリーム
/usr/bin/log stream --style compact \
  --predicate 'eventMessage CONTAINS "Sandbox:" AND eventMessage CONTAINS "deny("'
```

### フィルタリング手法

#### PID パターンでフィルタ

```bash
/usr/bin/log stream --style compact \
  --predicate 'eventMessage CONTAINS "Sandbox: 2.1.34(" AND eventMessage CONTAINS "deny("'
```

#### カーネルレベルの拒否を監視

```bash
/usr/bin/log stream --style compact \
  --predicate '(processID == 0) AND (senderImagePath CONTAINS "/Sandbox")'
```

### ノイズ削減

- dtracehelper や Apple 独自サービスなどの一般的なフォルスポジティブを除外
- `DYLD_USE_DTRACE=0` で dtrace を抑制可能

### 拒否ログからポリシールールへの変換

| ログのフォーマット | sandbox ポリシー allow ルール |
|-------------------|------------------------------|
| ファイル操作 deny | `(allow <operation> (literal "<path>"))` |
| sysctl deny | `(allow sysctl-read (sysctl-name "<name>"))` |
| mach-lookup deny | `(allow mach-lookup (global-name "<name>"))` |

### プロファイルの段階的構築

1. 最小構成から始める：
```
(version 1)
(deny default)
```

2. 各 deny をマッピングして allow ルールを追加
3. フルツールチェーンワークフローをテスト（子プロセスはサンドボックスポリシーを継承するため）

## テストフレームワーク

### 前提条件

- `sandbox-exec` が使える macOS ホスト
- 既存のサンドボックスセッション外で実行する必要がある

### テストスイート

メインのエントリポイント: `./tests/run.sh`

```bash
# 個別スイート実行
./tests/run.sh policy
./tests/run.sh surface
./tests/run.sh e2e
./tests/run.sh all

# 個別テストファイルの実行
bats tests/policy/integrations/docker.bats
```

### テストディレクトリ構成

- `tests/policy/` — ポリシールールテスト
- `tests/surface/` — サーフェステスト
- `tests/e2e/` — E2E テスト

### E2E テスト

`tmux` 配下で実際のエージェント TUI を Safehouse 経由で駆動し、起動・準備状態・基本的なプロンプトラウンドトリップをカバー。

テスト対象エージェント: aider, amp, claude-code, cline, codex, gemini, goose, kilo-code, opencode, pi

### テスト用依存関係のインストール

```bash
# Homebrew
brew install bats-core parallel tmux node

# エージェント
brew install aider block-goose-cli

# npm パッケージ
npm install -g @anthropic-ai/claude-code @anthropic-ai/claude-code-mcp-client \
  @anthropic-ai/claude-code-mcp-server @anthropic-ai/mcp-server-claude-code \
  @google/gemini-cli kilocode @anthropic-ai/pi @openai/codex amp-cli \
  @anthropic-ai/cline opencode-ai
```

### API キー

必要なプロバイダーキー：
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

キーやバイナリが欠如している場合、テストはクリーンにスキップされる。

### 統合テストの注意

ブラウザツール関連のテストは `agent-browser` と Playwright の `chromium-headless-shell` に依存する場合がある。CI では自動インストールされ、依存関係が欠如している場合はグレースフルにスキップされる。
