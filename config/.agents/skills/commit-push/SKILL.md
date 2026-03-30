---
name: commit-push
description: Conventional Commits メッセージを自動生成し、必要なら doc-updater skill を呼び出してからコミットと push を行うスキル。コミットしたい時、pushしたい時、ドキュメント更新込みでコミットしたい時に使用する。
---

# commit-push

## 概要

ステージング済みの変更から Conventional Commits メッセージを作り、必要ならドキュメントも更新してからコミットと push を行う。本文は orchestration だけを持ち、詳細ルールは必要なタイミングで supporting file を読む。

## 要件

- 返答とコミットメッセージは日本語
- 敬語は使わない
- Conventional Commits 形式にする
- 破壊的な操作（`reset` `clean` `rebase` `push --force` など）はしない

## supporting files

- コミットメッセージ profile 一覧: [`references/commit-message-profiles.md`](references/commit-message-profiles.md)
- doc-updater skill 本体: [`../doc-updater/SKILL.md`](../doc-updater/SKILL.md)

## 手順

### ステップ1: ステージング確認

1. `git diff --cached --name-only` でステージング済みファイルを確認する
   - 1つもステージングされていない場合は `git add -A` ですべてステージングする
   - 一部ステージング済みで一部未ステージングの場合は、ステージング済みの変更だけを対象にする
2. `git diff --cached --name-only --diff-filter=ACMRD` で最終的な対象差分があるか確認する
3. 変更が無い場合は、その旨を伝えて終了する

### ステップ2: ドキュメント自動更新

1. このセッション内で既にドキュメント更新を実行した、または更新不要と判断済みならこのステップをスキップする
2. ドキュメントファイル（`AGENTS.md` `CLAUDE.md` `GEMINI.md` `README.md` `docs/**/*.md` など）がすでにステージされている場合は、今回の変更で追加の更新が必要かだけ確認し、不要ならこのステップをスキップする
3. スキップしない場合は、最初に [`../doc-updater/SKILL.md`](../doc-updater/SKILL.md) を source of truth として扱う
4. `git diff --cached --name-only --diff-filter=ACMRD` で staged file list を、`git diff --cached --diff-filter=R --name-status` と `git diff --cached --diff-filter=D --name-only` で rename/delete context を収集する
5. 実行環境が `doc-updater` を別 skill として明示呼び出しできる場合は、それを明示的に呼ぶ
   - 対象は `git diff --cached` だけに限定する
   - staged file list と rename/delete context を渡す
   - 呼び出し元に学びや補足文脈があれば、その反映も依頼する
6. skill の明示呼び出しができない runtime では、`doc-updater` を実行できる仕組みがあればそれを使う。無ければ [`../doc-updater/SKILL.md`](../doc-updater/SKILL.md) を読んで同じ手順を inline で実行する
7. ドキュメントを更新した場合は `git add` でステージングし、更新不要なら「ドキュメント更新は不要」と判断して次に進む

### ステップ3: コミットメッセージ生成 & push

1. runtime を次の順で判定する
   - `CLAUDECODE=1` なら `claude-code` profile を選ぶ
   - `GEMINI_CLI=1` なら `gemini-cli` profile を選ぶ
   - それ以外は unknown runtime として扱う
2. unknown runtime の場合は、自分の実行環境を自分で確信を持って識別できるなら対応する profile を選ぶ。確信できない場合は `generic-fallback` を選ぶ
3. [`references/commit-message-profiles.md`](references/commit-message-profiles.md) を読み、以下の優先順位で profile を 1 つ選ぶ
   - env marker で確定できる profile
   - 実行中エージェントが自分の runtime identity から確信を持てる profile
   - `generic-fallback`
4. `git diff --cached` で最終的なステージング済み差分を確認し、Conventional Commits のコミットメッセージを 1 つ作る
   - 形式: `<type>(<scope>): <subject>`
   - type は `feat|fix|docs|refactor|perf|test|build|ci|chore` から選ぶ
   - scope は分かる場合のみ付ける。不明なら省略する
   - subject は短く要点のみ。末尾に句点は付けない
   - body は必要な場合のみ付ける
   - 選んだ profile の `commit trailer` が `なし` なら trailer を付けない
   - 選んだ profile に `subject/body 追加ルール` があればそれに従う
5. `git diff --cached --name-only --diff-filter=ACMRD` を再確認し、差分が無ければ終了する
6. 生成したメッセージでコミットし、現在のブランチを push する
   - body と trailer がある場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>" -m "<body>" -m "<trailer>"`
   - trailer だけある場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>" -m "<trailer>"`
   - trailer がなく body だけある場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>" -m "<body>"`
   - trailer も body も無い場合: `SKIP_DOC_UPDATER=1 git commit -m "<type>(<scope>): <subject>"`
   - `git push`

## 注意

- unknown runtime では、コミットメッセージに実行環境の固有名詞を勝手に入れない
- push が失敗したら、エラー要点と次のアクション候補だけを伝えて終了する
