---
name: implement
description: 確定した要件を、実装、検証、atomic commit、push、独立レビュー、必要な計画アーカイブまで完遂するスキル。ユーザーが「実装して」「実装開始して」「このプランを実装して」「続きを実装して」「最後まで仕上げて」など、変更の実装開始・継続・完了を求めたときに使う。計画があれば Plan mode、ユーザーが計画を省略して直接実装すると決めた場合は Direct mode で進める。計画作成、設計相談、説明、レビューだけを求められた場合は使わない。実装指示は検証済み成果物のcommitとpushを含む承認として扱う。
compatibility: Gitリポジトリと、tdd・commit-pushスキル、独立したreviewerを起動できる実行環境を前提とする。
---

# Implement

確定した要件を、検証とレビューを通った状態でリモートへ反映する。詳細なテスト品質は `tdd`、staging、commit、push、ドキュメント更新は [`commit-push`](../commit-push/SKILL.md) を正本とし、このスキルは実行順序と完了条件を管理する。

## Authorization

このスキルを起動する実装指示は、次を承認したものとして扱う。

- 検証済みの成果物単位でatomic commitを作る。
- 各commitの直後にpushする。
- レビュー指摘のうち、スコープ内のblocking/highを修正してcommit、pushする。
- 全完了後、対象プランを独立したcommitでアーカイブしてpushする。

force push、rebase、amend、履歴の書き換え、破壊的な削除、要件外の変更、ユーザーや別プロセスの変更は承認に含まれない。

## Entry modes

ユーザーが選んだ経路を使う。エージェントが変更規模を理由に計画を省略してはならない。

### Plan mode

次の順で対象プランを決める。

1. ユーザーが指定したパス。
2. 現在の会話で作成または選択したプラン。
3. `docs/plans/` 直下にある未アーカイブの計画が1件だけなら、その計画。

複数の候補が残る場合は、編集前に対象を一つだけ確認する。プランのRequirements、Decisions、Out of Scope、Contracts、Tasks、Validationを実装仕様とする。

### Direct mode

ユーザーが「このまま実装して」などと指示し、計画を作らず進む経路を選んだ場合に使う。現在の会話、`dig`で合意した決定、ユーザーが提示した完了条件を実装仕様とする。計画ファイルは作成せず、アーカイブもしない。

要件、Out of Scope、公開契約、テスト境界に未確定事項が残る場合は、実装を始めず一度に一つだけ確認する。複数領域への波及や新しい設計判断が判明し、直接実装の前提が崩れた場合は停止して`plan`の利用を提案する。

## Preflight

編集前に次を行う。

1. 対象ファイルへ適用される`AGENTS.md`などの指示を読む。
2. Plan modeではプラン全体を読み、Direct modeでは会話中の決定事項と対象外を整理する。
3. `git status --short`、`git diff --cached`、`git diff`でstaged、unstaged、untrackedを確認する。
4. この実装が所有する変更パスと、開始前から存在する変更パスを区別する。
5. 既存のstaged変更がある場合は、所有権が明確でも開始せずユーザーに確認する。
6. 既存のunstaged/untracked変更が対象ファイルと重なる場合は開始せず確認する。重ならない変更は残したまま続行し、commit対象から除外する。
7. レビュー用に開始時のbase commitを記録する。
8. 成果物の数と依存関係を確認し、必要な場合だけユーザー可視のtodoを作る。

## TDD

自動テストで観測できる振る舞いには、`tdd`スキルを読み、確定済みのtest seamでRed → Greenを繰り返す。

- プランのTesting Decisionsにあるseam、または`dig`で合意したseamは確認済みとして扱う。
- seamが決まっておらず、選択によって公開インターフェースやテスト範囲が変わる場合は確認する。
- 一つの振る舞いについて、失敗するテストを確認してから、それを通す最小限の実装を書く。
- 先のテストや機能をまとめて実装せず、vertical sliceごとに進める。
- リファクタリングはRed → Greenの途中に混ぜず、レビュー段階で行う。

文書、設定、生成物など、失敗テストを作る意味がない変更にはRedを強制しない。Plan modeでは理由と代替検証を該当タスクへ記録し、Direct modeでは進捗報告に示してから、構文検査、差分比較、実コマンド確認など最も近い検証を行う。

## Delivery loop

プランタスク、またはDirect modeのレビュー可能な成果物ごとに次を繰り返す。

1. 対象成果物をin progressにする。
2. テスト可能な振る舞いはTDDで実装する。非テスト変更は定めた代替検証を使う。
3. 成果物に最も近いfocused validationを実行する。
4. validationが成功した後にだけ進捗を完了へ更新する。
5. Plan modeでは、実際の変更ファイル、軽微な実装差分、検証結果の要点を該当タスクへ反映する。要件、Out of Scope、公開契約の変更は先にユーザーへ確認する。
6. 下記の条件に当てはまる場合はcommit前にタスク差分を自己レビューし、明らかな欠陥、スコープ外変更、テスト漏れを直してfocused validationを再実行する。
7. [`commit-push`](../commit-push/SKILL.md)を読み、この成果物だけをcommit + pushモードで処理する。pushが成功するまで成果物を完了扱いにしない。

原則は1プランタスクにつき1commitとする。タスクが一つのreview/revert単位として大きすぎる場合は分割し、小さく不可分な隣接タスクは統合できる。分割または統合した場合は、Plan modeの該当タスクへcommitとの対応を記録する。Direct modeでは作業テーマ単位で分ける。

### Task-level self-review

次のいずれかに当てはまる場合に行う。

- 複数タスクまたは複数コンポーネントにまたがる。
- 公開契約、データ移行、永続化、並行処理を変更する。
- 認証、認可、セキュリティ、課金、データ損失に関係する。
- focused validationだけでは回帰範囲を十分に絞れない。

局所的で既存パターンに沿い、強い自動テストがある変更では省略できる。最終の独立レビューは省略しない。

## Progress

### Plan mode

- TaskのValidationが成功したら、Progressの対応項目を完了にする。
- 計画との差異は作業ログとして羅列せず、変更ファイル、判断に影響する差分、検証結果だけを残す。
- Final Validationは実行して成功した項目だけを完了にする。
- 失敗、未検証、未解決の項目を完了にしない。

### Direct mode

- 3件以上の意味ある成果物や依存関係がある場合はtodoを使う。
- 小さな変更ではチャットの進捗だけを使う。
- Git履歴を永続的な実装記録とし、進捗記録のためだけの文書は作らない。

## Final review

全成果物のpush後に、関連するfocused test、full test、lint、typecheck、build、手動確認などのfinal validationを実行する。適用できない標準検証は、理由を明記してN/Aとする。

次に、実装を担当していない別コンテキストのreviewerへ以下を渡す。

- Plan modeのプラン、またはDirect modeで確定した要件と対象外。
- base commitから現在のHEADまでの実装差分とcommit一覧。
- 実行した検証と結果。
- 既存の無関係なworktree変更の一覧。

reviewerには正確性、回帰、セキュリティ、仕様適合性、テスト不足を重要度順に報告させる。

- スコープ内のblocking/highは自動で修正する。
- 要件、Out of Scope、公開契約の変更が必要な指摘はユーザーへ確認する。
- 軽微な指摘は、修正による複雑化と保守性を比較して判断する。
- 修正にはTDDと同じ検証規則を適用し、atomic commitを作ってpushする。
- 影響範囲の検証とfinal validationを再実行し、reviewerへ再レビューを依頼する。
- 同じblocking/highが解消できない場合は停止し、完了を主張しない。

独立したreviewerを利用できない場合は、その制約を報告して未完了として停止する。自己レビューだけで代替せず、Plan modeの計画はアーカイブしない。

レビューと再検証が終わったら`git status --short`、`git diff --cached`、`git diff`を再確認する。Preflightで記録した既存変更を除き、implementation-ownedなstaged、unstaged、untracked変更が残っている場合は、必要な検証とcommit + pushを終えるまで完了を主張しない。

## Plan archive

Plan modeだけで行う。次の条件がすべて成立した後、計画を同名のまま`docs/plans/archived/`へ移す。

- すべてのタスクと、Plan archive自体を除くFinal Validationが完了している。
- Requirement Coverageと実際の変更が一致している。
- final validationが成功している。
- 独立レビューに未解決のblocking/highがない。
- レビュー修正後の再検証と再レビューが完了している。
- 実装commitがすべてpush済みである。
- Preflightで記録した既存変更を除き、implementation-ownedな未commitの変更が残っていない。

アーカイブ移動だけを独立した最終commitにし、[`commit-push`](../commit-push/SKILL.md)でpushする。アーカイブ前に条件を満たせなくなった場合は、計画を未アーカイブの場所へ残す。

## Blockers

タスク途中でvalidation失敗、所有権衝突、未確定仕様、解決できないレビュー指摘などのblockerが残った場合は、未完成の変更をcommitもpushもしない。変更はローカルに残し、Plan modeでは次を計画へ記録する。

- 失敗した検証と結果。
- 判明した原因。
- 未完了の範囲。
- 再開に必要な判断または条件。

pushだけが失敗した場合は、作成済みのローカルcommitを戻さない。エラーと再実行条件を報告し、push成功まで次の成果物とPlan archiveへ進まない。

## Completion report

最終報告は次の順で簡潔にまとめる。

1. 完了または未完了の結論。
2. 実装した成果物と主要commit。
3. 検証結果。
4. 独立レビューと修正結果。
5. Plan modeではアーカイブ先。Direct modeでは計画なしで完了した旨。
6. 残した無関係なworktree変更または未解決blocker。
