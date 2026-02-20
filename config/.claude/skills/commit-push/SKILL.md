---
name: commit-push
description: Conventional Commits メッセージを自動生成し、doc-updater によるドキュメント自動更新を含めてコミット＆pushする。コミットしたい時、pushしたい時に使用する。
model: claude-haiku-4-5
disable-model-invocation: true
allowed-tools: Bash(git:*), Task(doc-updater)
---

# コミットメッセージ自動生成 & push

ステージング済みの変更から Conventional Commits メッセージを生成し、ドキュメント自動更新を含めてコミット＆push する。

## 要件

- 返答・コミットメッセージは日本語
- 敬語は使わない
- Conventional Commits 形式にする

## 手順

### ステップ1: ステージング確認

1. `git diff --cached --name-only` でステージング済みファイルを確認する
   - 1つもステージングされていない場合 → `git add -A` ですべてステージングする
   - 一部ステージング済み、一部未ステージングの場合 → ステージング済みのファイルのみ対象とする（追加ステージングはしない）
2. ステージングされている変更があるか確認する。変更が無い場合はその旨を伝えて終了する

### ステップ2: ドキュメント自動更新

doc-updater サブエージェント（モデルは必ず haiku を使う）に以下を依頼する:

「ステージ済みの変更（`git diff --cached`）を確認し、必要に応じてドキュメントを更新してください。」

doc-updater がファイルを変更した場合:
- `git diff --name-only` で doc-updater が変更したファイルを特定する
- それらを `git add` でステージングに追加する

### ステップ3: コミットメッセージ生成 & push

1. `git diff --cached` で最終的なステージング済み差分を確認し、Conventional Commits のコミットメッセージを1つ作る
   - 形式: `<type>(<scope>): <subject>`
   - type は `feat|fix|docs|refactor|perf|test|build|ci|chore` から選ぶ
   - scope は分かる場合のみ付ける（例: `commands`, `config` など）。不明なら省略可
   - subject は短く要点のみ。末尾に句点は付けない
   - body は必要な場合のみ。変更理由・背景・注意点を書く（箇条書き可）
2. 生成したコミットメッセージを使ってコミットし、現在のブランチを push する
   - body がある場合: `git commit -m "<subject>" -m "<body>" -m "Co-Authored-By: Claude Code <noreply@anthropic.com>"`
   - body が無い場合: `git commit -m "<subject>" -m "Co-Authored-By: Claude Code <noreply@anthropic.com>"`
   - `git push`

## 注意

- 破壊的・危険な操作（reset / clean / rebase / force push 等）はしない
- push が失敗したら、エラー要点と次のアクション候補（例: 認証 / remote / ブランチ名確認）を提示して終了する
