---
name: commit-push
description: Conventional Commits メッセージを自動生成し、doc-updater によるドキュメント自動更新を含めてコミットと push を行うスキル。コミットしたい時、pushしたい時、ドキュメント更新込みでコミットしたい時に使用する。
---

# コミットメッセージ自動生成 & push

## 概要

ステージング済みの変更から Conventional Commits メッセージを作り、必要ならドキュメントも更新してからコミットと push を行う。

## 要件

- 返答とコミットメッセージは日本語
- 敬語は使わない
- Conventional Commits 形式にする
- コミットメッセージ本文の末尾に `Co-Authored-By: Codex <noreply@openai.com>` を追加する

## 手順

### ステップ1: ステージング確認

1. `git diff --cached --name-only` でステージング済みファイルを確認する
   - 1つもステージングされていない場合は `git add -A` ですべてステージングする
   - 一部ステージング済みで一部未ステージングの場合は、ステージング済みの変更だけを対象にする
2. `git diff --cached --name-only --diff-filter=ACMRD` で最終的な対象差分があるか確認する
3. 変更が無い場合は、その旨を伝えて終了する

### ステップ2: ドキュメント自動更新

1. このセッション内で既に `doc-updater` を実行した、または更新不要と判断済みならこのステップをスキップする
2. スキップしない場合は `doc-updater` サブエージェントに以下を依頼する

   「ステージ済みの変更（`git diff --cached`）を確認し、必要に応じてドキュメントを更新してください。」

3. `doc-updater` がファイルを変更した場合は、変更したファイルを `git add` でステージングに追加する
4. 更新不要なら「ドキュメント更新は不要」と判断して次に進む

### ステップ3: コミットメッセージ生成 & push

1. `git diff --cached` で最終的なステージング済み差分を確認し、Conventional Commits のコミットメッセージを1つ作る
   - 形式: `<type>(<scope>): <subject>`
   - type は `feat|fix|docs|refactor|perf|test|build|ci|chore` から選ぶ
   - scope は分かる場合のみ付ける。不明なら省略する
   - subject は短く要点のみ。末尾に句点は付けない
   - body は必要な場合のみ付ける
   - 本文末尾に `Co-Authored-By: Codex <noreply@openai.com>` を付ける
2. `git diff --cached --name-only --diff-filter=ACMRD` を再確認し、差分が無ければ終了する
3. 生成したメッセージでコミットし、現在のブランチを push する
   - body がある場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>" -m "<body>" -m "<Co-Authored-By 行>"`
   - body が無い場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>" -m "<Co-Authored-By 行>"`
   - `git push`

## 注意

- `doc-updater` サブエージェントは `.codex/agents/doc-updater.toml` で定義する
- `doc-updater` サブエージェントが利用できない環境ではこのスキルを使わない
- 承認フローがある環境では、`git add` `git commit` `git push` に必要な承認をその環境のルールに従って取得する
- 破壊的な操作（`reset` `clean` `rebase` `push --force` など）はしない
- push が失敗したら、エラー要点と次のアクション候補だけを伝えて終了する
