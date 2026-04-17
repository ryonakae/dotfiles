---
name: commit-push
description: Conventional Commits メッセージを自動生成し、必要なら doc-updater skill を呼び出してからコミットと push を行うスキル。コミットしたい時、pushしたい時、ドキュメント更新込みでコミットしたい時に使用する。ユーザーが /commit-push と明示的に指示した場合を除き、自律的に起動しない。
disable-model-invocation: true
---

# commit-push

## 概要

ステージング確認 → ドキュメント更新（doc-updater に委譲）→ コミット＆push を順に行う。コミットメッセージの runtime 別ルールは [`references/commit-message-profiles.md`](references/commit-message-profiles.md) に分離している。

## 手順

### ステップ1: ステージング確認

1. ステージング済みファイルを確認する。何もなければ `git add -A` で全てステージングする。一部だけステージング済みなら、ステージング済みの変更だけを対象にする。
2. 変更が無い場合は終了する。

### ステップ2: ドキュメント自動更新

1. このセッション内で既にドキュメント更新済み、または更新不要と判断済みならスキップする
2. ドキュメントファイルがすでにステージされていて追加更新が不要ならスキップする
3. doc-updater をサブエージェントで実行する（可能なら軽量モデルを使う）。サブエージェントへの指示:
   - doc-updater スキルを読んで従う
   - 対象は staged change のみ
   - commit/push は行わない
   - 更新したら git add する
   サブエージェントが使えない場合は doc-updater スキルを inline で実行する。
4. 更新不要なら次に進む

### ステップ3: コミットメッセージ生成 & push

1. [`references/commit-message-profiles.md`](references/commit-message-profiles.md) を読み、選択順に従って profile を 1 つ選ぶ
2. `git diff --cached` で差分を確認し、コミットメッセージを作る
   - Conventional Commits 形式（`<type>(<scope>): <subject>`）
   - type: `feat|fix|docs|refactor|perf|test|build|ci|chore`
   - scope は分かる場合のみ。subject の末尾に句点は付けない
   - body は必要な場合のみ
   - profile の trailer・追加ルールに従う
3. `git commit -m "..."` でコミットする。body や trailer がある場合は別の `-m` で渡す。
4. `git push` する。失敗したらエラー要点と次のアクション候補だけを伝えて終了する。

## 注意

- 破壊的な操作（`reset` `clean` `rebase` `push --force` など）はしない
