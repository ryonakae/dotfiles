---
name: commit-push
description: Conventional Commits メッセージを自動生成し、`git diff --cached` を元に doc-updater 手順を同一エージェントで実行してからコミットと push を行うスキル。コミットしたい時、pushしたい時、ドキュメント更新込みでコミットしたい時に使用する。
---

# コミットメッセージ自動生成 & push

## 概要

ステージング済みの変更から Conventional Commits メッセージを作り、必要ならドキュメントも更新してからコミットと push を行う。`doc-updater` はサブエージェントや外部 CLI として起動せず、同一エージェントが `references/doc-updater.md` の手順をそのまま実行する。

## 要件

- 返答とコミットメッセージは日本語
- 敬語は使わない
- Conventional Commits 形式にする

## 手順

### ステップ1: ステージング確認

1. `git diff --cached --name-only` でステージング済みファイルを確認する
   - 1つもステージングされていない場合は `git add -A` ですべてステージングする
   - 一部ステージング済みで一部未ステージングの場合は、ステージング済みの変更だけを対象にする
2. `git diff --cached --name-only --diff-filter=ACMRD` で最終的な対象差分があるか確認する
3. 変更が無い場合は、その旨を伝えて終了する

### ステップ2: ドキュメント自動更新

1. このセッション内で既にドキュメント更新を行った、または更新不要と判断済みならこのステップをスキップする
2. スキップしない場合は `references/doc-updater.md` を読んで、`git diff --cached` を基準に更新要否を判断する
3. ドキュメントを変更した場合は、変更したファイルを `git add` でステージングに追加する
4. 更新不要なら「ドキュメント更新は不要」と判断して次に進む

### ステップ3: コミットメッセージ生成 & push

1. `git diff --cached` で最終的なステージング済み差分を確認し、Conventional Commits のコミットメッセージを1つ作る
   - 形式: `<type>(<scope>): <subject>`
   - type は `feat|fix|docs|refactor|perf|test|build|ci|chore` から選ぶ
   - scope は分かる場合のみ付ける。不明なら省略する
   - subject は短く要点のみ。末尾に句点は付けない
   - body は必要な場合のみ付ける
2. `git diff --cached --name-only --diff-filter=ACMRD` を再確認し、差分が無ければ終了する
3. 生成したメッセージでコミットし、現在のブランチを push する
   - body がある場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>" -m "<body>"`
   - body が無い場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>"`
   - `git push`

## 注意

- `references/doc-updater.md` の処理は自分で実行する。別エージェントへの委譲や専用 CLI 呼び出しはしない
- 承認フローがある環境では、`git add` `git commit` `git push` に必要な承認をその環境のルールに従って取得する
- 破壊的な操作（`reset` `clean` `rebase` `push --force` など）はしない
- push が失敗したら、エラー要点と次のアクション候補だけを伝えて終了する
