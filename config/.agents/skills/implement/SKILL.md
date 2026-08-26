---
name: implement
description: 確定した要件を実装、検証、atomic commit、独立レビュー、計画アーカイブ、最終 push まで完遂する。計画があれば Plan mode、ユーザーが計画を省略して直接実装すると決めた場合は Direct mode で進める。
compatibility: Gitリポジトリと、tdd・commit-pushスキル、独立したreviewerを起動できる実行環境を前提とする。
disable-model-invocation: true
---

# Implement

確定した要件を、検証と独立レビューを通った状態で remote へ反映する。テストの進め方は `tdd`、staging・commit・文書更新は [`commit-push`](../commit-push/SKILL.md) が正本。このスキルが決めるのは実行順序、reviewer との契約、停止条件の 3 つだけ。

## 原則

- **commit は成果物ごとに local で積み、push は最後に 1 回。** 途中で push すると、レビューで直すべき commit がすでに公開されていて取り消せず、修正 commit が上乗せされて履歴が汚れる。
- **独立レビューは 1 回、自動修正は 2 cycle まで。** reviewer は新しい所見を無限に出せる。上限がなければ収束の判断がなく、修正 → 再レビューが際限なく続く。
- **reviewer の重要度は提案であって命令ではない。** 実装側が Requirements と照合して採否を決める。reviewer は計画にない互換性要件や設計上の好みを blocking と呼びがちで、それに従うと要件外の作業が生まれる。
- **仕様・所有権・予算のどれかが不確定なら、編集や push の前に止めて聞く。** 推測で進めた分は手戻りになる。

## Authorization

このスキルの起動は次の承認として扱う。

- 検証済みの成果物単位で local atomic commit を作る。
- スコープ内の blocking/high を 2 cycle 以内で修正し、correction commit を作る。
- 全ゲート通過後、Plan archive を含む commit 列を current branch へ 1 回 push する。

force push、amend、rebase、squash、履歴の書き換え、破壊的な削除、要件外の変更、ユーザーや別プロセスの変更、feature branch の作成は承認に含まれない。default branch でも同じゲートを使う。

## Entry modes

ユーザーが選んだ経路を使う。変更規模を理由にエージェントが計画を省略してはならない。

**Plan mode** — 対象は、ユーザー指定パス → 現在の会話で作成・選択した Plan → `docs/plans/` 直下に未アーカイブが 1 件だけならそれ、の順で決める。複数残るなら確認する。Plan の Requirements、Decisions、Out of Scope、Contracts、Tasks、Validation を実装仕様とする。

**Direct mode** — ユーザーが計画を作らず実装すると決めた場合。会話、`dig` の合意、ユーザーの完了条件を実装仕様とする。計画ファイルは作らず、アーカイブもしない。複数領域への波及や新しい設計判断が判明したら停止して `plan` を提案する。

## Preflight

編集前に次を確認する。

1. 対象ファイルに適用される `AGENTS.md` などの指示。
2. Plan 全体、または Direct mode の決定事項と対象外。
3. `git status --short`、`git diff --cached`、`git diff`。既存の staged 変更があれば開始せず確認する。unstaged/untracked が対象ファイルと重なる場合も確認する。重ならない変更は残し、commit 対象から除外する。
4. upstream、ahead/behind、push 対象範囲。upstream が未設定・曖昧、diverged、開始前から未 push commit がある場合は、それを自分の成果として push しないよう確認する。
5. review 用の base commit を記録する。

必須 validation が remote CI やデプロイでしか実行できず、Plan やユーザーがその扱いを決めていない場合も、編集前に確認する。

## 成果物ごとの実装

Plan の Task、または Direct mode のレビュー可能な単位ごとに繰り返す。原則 1 Task = 1 commit。大きすぎれば分割、不可分な隣接 Task は統合してよい。

1. 自動テストで観測できる振る舞いは `tdd` を読み、Red → Green を vertical slice ごとに進める。合意済みの test seam は確認済みとして扱い、seam の選択が公開 interface やテスト範囲を変えるなら確認する。文書・設定・生成物には Red を強制せず、構文検査や差分比較など最も近い validation を使う。
2. 同じ context で self-review する。要件対応、scope、明白な欠陥、テスト漏れを見て、必要な refactor はここで行う。独立レビューに refactor を持ち込むと cycle を消費する。
3. 成果物に最も近い focused validation を実行する。
4. Plan mode では、変更ファイル、判断に影響する差分、validation 結果だけを該当 Task に反映し、Progress を更新する。Requirement、Out of Scope、Contract はユーザー承認なしに変えない。
5. [`commit-push`](../commit-push/SKILL.md) の **commit-only** で、この成果物と Plan 更新だけを local commit する。commit 成功で Task 完了。

Direct mode で成果物が 3 件以上または依存関係があれば todo を使う。進捗記録だけの文書は作らない。

## 独立レビュー

全成果物を commit した後、Plan や project の標準 validation（test、lint、typecheck、build のうち local で非対話・非破壊に実行できるもの）を実行し、worktree に実装由来の residue がないことを確認してから、reviewer に渡す。

Plan mode では必須。Direct mode で省略できるのは、変更がすべて非実行の prose/comment で、契約や運用手順を定義しない場合だけ。

reviewer は実装を担当していない **read-only の context を 1 つ**使い、re-review も同じ context で続ける。同じ reviewer が finding の履歴を持つことで、再レビューが差分に絞れる。model や thinking level は固定しない。渡すもの:

- Plan、または Direct mode で確定した Requirements、Contracts、Out of Scope。
- base から HEAD までの diff と commit 一覧。
- 実行した validation とその結果。
- 既存の無関係な worktree 変更。

reviewer には finding を `blocking/high` / `decision required` / `medium/low` / `pre-existing unrelated` に分けさせる。`blocking/high` には、違反する Requirement・Contract・Out of Scope・重大な安全性 invariant、対象箇所、具体的な失敗経路、今回の diff が問題を導入または到達可能にした根拠を必須とする。Requirement が足りず正解を決められない場合は、要件を補わず `decision required` にさせる。

### Triage

- 根拠を満たすスコープ内の `blocking/high` は採用し、同じ generation の分をまとめて修正する。
- 根拠不足、未合意の互換性・将来要件、設計上の好みは採用せず、理由を記録する。
- `decision required` は修正前に停止し、1 件ずつ確認する。
- `medium/low` は修正せず completion report に残す。
- `pre-existing unrelated` は報告のみ。ただし今回の diff が悪化させた、または到達可能にしたものは今回の finding として扱う。

reviewer 出力が証拠形式を満たさなければ、同じ context に 1 度だけ補足を求める。reviewer が使えなくなったら代替を 1 度だけ立て、Plan と finding 履歴を引き継ぐ。有効な独立レビューが得られなければ未完了で停止する。

## 修正 cycle

1 invocation で自動修正は **最大 2 cycle**。checkpoint、final review、final validation 起因を合算する。1 cycle は、採用した `blocking/high` をまとめて修正 → 影響範囲の validation → local correction commit → 同じ reviewer への scoped re-review、の一巡。

scoped re-review の対象は、既存 finding の解消、correction diff、その修正が直接影響する経路に限る。2 cycle を終えて `blocking/high` が残る場合は、明白な小修正でも 3 cycle 目に進まず、未解決 finding、根拠、対応案を示して停止する。

ユーザーが Requirement や Contract の変更を承認した場合は、Plan または合意を更新して影響範囲を実装・validation し、新仕様に対する full review を新しい 2 cycle 予算で行う。

## Final validation と delivery

`blocking/high` と `decision required` がなくなったら、review 前に成功した validation のうち入力と対象挙動が変わっていないものは再利用し、外部環境・手動確認が必要なものと、変更で無効になったものだけを実行する。substantive fix が必要になれば修正 cycle を 1 つ使う。

full suite の失敗が base でも再現し無関係と確認できても、自動修正、N/A 化、成功扱いはせず、受入条件を変えるかユーザーに確認する。

review と validation が同じ HEAD に対して有効になったら:

1. Plan mode では、review 対象 commit、採用した finding と correction commit、未解決なしの旨を gate summary として Plan に書き、同名のまま `docs/plans/archived/` へ移す。移動と summary を **1 つの archive commit** にまとめる（commit-push の commit-only を使う）。archive 後に管理用 commit を追加しない。
2. `git status --short`、`git diff --cached`、`git diff` を再確認する。実装由来の residue があれば validation と review へ戻る。
3. Preflight の push 範囲と upstream を再確認し、通常の `git push` で commit 列全体を 1 回 push する。

push 成功まで完了扱いにしない。push が失敗しても local commit は戻さず、エラーと再実行条件を報告する。

## 停止して確認する条件

- Requirement、Contract、Out of Scope、合意済み test seam の変更が必要になった。
- `decision required` が出た。
- 修正予算を使い切った。
- 有効な独立 reviewer が得られない。
- 所有権が衝突する（既存 staged、対象と重なる unstaged、開始前の未 push commit、曖昧な upstream）。
- 受入条件を満たせない validation 失敗が残った。

停止時は未完成の変更を push せず、未 commit の変更は local に残す。Plan mode では、失敗した validation、判明した原因、未完了の範囲、再開に必要な判断を Plan に記録する。

## Completion report

1. 完了または未完了の結論。
2. 実装した成果物と主要 commit。
3. validation 結果（実行・再利用・未実行）。
4. 独立レビュー、採用した finding、cycle 数、残した medium/low。
5. Plan mode では archive 先。Direct mode では Plan なしで完了した旨。
6. push 結果。
7. 残した無関係な worktree 変更または未解決 blocker。
