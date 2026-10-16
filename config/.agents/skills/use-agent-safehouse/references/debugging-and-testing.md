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

### 一次診断手順

問題発生時はこの順序で進める。

1. 失敗command、エラーに現れたpath・操作、実際の起動引数を確認する。単独の `safehouse` 呼び出しと、この環境のwrapperが生成するpolicyは異なる。deny対象の実秘密をprobeしない。
2. 同じ起動引数で `safehouse --stdout <command>` を使い、標準feature、grant、追加profile、terminal denyの順を確認する。`--stdout` はcommandを実行しない。`--explain` はstderrへサマリを出し、commandを指定すると実行もするので、拒否操作の再試行に使わない。
3. 必要なら上記の `/usr/bin/log stream` で既存の拒否ログを確認する。
4. 標準の `--enable` や既存grantで対応できるかを先に確認する。残るdenyとの衝突なら、理由と承認が必要な最小変更を提示する。denyログからallowを機械的に追加しない。
5. policy変更は次回起動で反映する。実行中のsandboxのpolicyは更新できない。

拒否された操作を無断で sandbox 外へ移さない。検証は変更に近い差分・構文・必要な smoke に絞る。

## テストフレームワーク

### 前提条件

- `sandbox-exec` が使える macOS ホスト
- 既存のサンドボックスセッション外で実行する必要がある

### Safehouse本体のテストスイート

以下はSafehouse本体リポジトリの手順であり、dotfilesの変更ごとの完了条件ではない。
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
