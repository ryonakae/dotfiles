# LLM を使ったカスタム sandbox-exec プロファイル生成ガイド

## 概要

Agent Safehouse は LLM（Claude, Codex, Gemini 等）を使って、マシン固有の最小権限 `.sb` サンドボックスプロファイルを生成する仕組みを提供している。

## 参照するソースファイル

**重要**: `dist/` ディレクトリではなく `profiles/` と `bin/` を source of truth として使用する。`dist/safehouse.sh` は生成済みアーティファクトであり、プロファイル設計の参照元としては不適切。

LLM は以下の Agent Safehouse リポジトリのソースを参照してプロファイルを生成する：

- `00-base.sb` — ベースプロファイル構造
- `10-system-runtime.sb` — システムランタイム
- `20-network.sb` — ネットワークポリシー
- ツールチェーン、統合、エージェント固有モジュール
- ポリシー組み立て用シェルスクリプト

## 自動検出フェーズ

LLM は以下を検出する：

1. ホームディレクトリパス
2. アクティブなシェルと設定ファイルの場所
3. インストール済みツールチェーンと CLI エージェント
4. 一般的なグローバル dotfile（`.gitconfig`, `.npmrc` 等）

## 検出コマンド例

```bash
echo $HOME
echo $SHELL
ls -la ~/.config/
which node python3 go rustc bun uv
ls -la ~/.gitconfig ~/.npmrc ~/.yarnrc.yml 2>/dev/null
which claude aider codex 2>/dev/null
git -C ~/[project] worktree list 2>/dev/null
```

## 単一フォローアップ質問

複数の質問ではなく、以下をまとめて1回の質問に集約する：
- プロジェクトディレクトリ
- パスアクセスレベル
- 検出項目への修正

## 成果物

プロファイル生成で以下が出力される：

1. **完全な `.sb` プロファイルファイル** — 各アクセスグラントの説明付き
2. **ラッパースクリプト**（オプション） — `sandbox-exec` 起動用
3. **シェル設定スニペット** — エージェントショートカット用
4. **インストール・検証チェックリスト**

## 設計原則

- **deny-by-default** ルール
- グローバル dotfile への最小限のアクセス
- 広い権限ではなく明示的なサブパスルール
- コメントによる明確な監査可能性
