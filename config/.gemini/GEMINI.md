# GEMINI.md

## 言語

- ユーザーへのレスポンス、アーティファクト、コミットメッセージ、コード内のコメントは必ず日本語で行う
- システムエラーやログの引用は原文のままにする

## 実装時の注意点

- 常に既存コードの設計や記法を参考にする
- コメントを残す場合は、コードから自明な処理の説明コメントは残さず、複雑なアルゴリズム、特定のビジネスロジック、設計上のトレードオフ、将来の変更可能性など、コードだけでは読み取れない「なぜ（Why）」や背景（Context）を説明するコメントだけを、必要な箇所に記述

## Pythonの実行

- CLIツールの実行: `uvx <パッケージ名>` を使う（グローバルインストール不要で一時環境から実行される）
  - 例: `uvx ruff check .`, `uvx black .`, `uvx mypy .`
- スクリプトの実行: `uv run` を使う
  - 例: `uv run script.py`, `uv run python script.py`
- パッケージの追加: `uv add` / `uv pip install` を使い、`pip install` は使わない

## ライブラリ/API/SDKの利用

- `find-docs` スキルを呼び出し、最新のドキュメントを取得する
- 呼び出せない場合は Context7 MCP を使う

## Webページの取得

- Webページの内容を取得する場合、コーディングエージェントに標準で内蔵されている `WebSearch`, `WebFetch` のようなツールだと `403` エラーで失敗する場合がある。その場合は `agent-browser` を使う

## Google Workspace CLI (gws)

- `gws` CLI は人間の Google アカウントを共有する。Gmail / Calendar / Drive の削除など破壊的操作は実行前にユーザー確認を取る

## コミットメッセージの生成

- 返答・コミットメッセージは日本語
  - 敬語は使わない
- Conventional Commits 形式にする

### 手順

1. ステージングされているファイルを確認する
   - 1つもステージングされていない場合 → すべてのファイルを対象にする
   - 一部ステージング済み、一部未ステージングの場合 → ステージング済みのファイルのみ対象とする
2. 変更・差分を確認し、Conventional Commits のコミットメッセージを生成
   - 形式: `<type>(<scope>): <subject>`
   - type は `feat|fix|docs|refactor|perf|test|build|ci|chore` から選ぶ
   - scope は分かる場合のみ付ける（例: `commands`, `config` など）。不明なら省略可
   - subject は短く要点のみ。末尾に句点は付けない
   - body は必要な場合のみ。変更理由・背景・注意点を書く（箇条書き可）
