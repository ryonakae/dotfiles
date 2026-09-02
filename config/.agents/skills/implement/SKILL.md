---
name: implement
description: ユーザーがimplementスキルの実行を明示した場合、「このPlanを実装して」のように承認済みPlanの実行を指示した場合、または「計画を作らずそのまま実装して」と明示した場合に、実装、検証、atomic commit、独立レビュー、計画アーカイブ、最終pushまでを完遂する。それ以外の一般的な小規模実装や修正、要件・設計が未確定の依頼、調査、レビュー、計画作成・説明だけには使わない。
compatibility: Gitリポジトリと、tdd・commit-pushスキル、独立したreviewerを起動できる実行環境を前提とする。
---

# Implement

確定した要件を、検証と独立レビューを通った状態で remote へ反映する。テストの進め方は `tdd`、staging・commit・文書更新は [`commit-push`](../commit-push/SKILL.md) が正本で、このスキルは委譲する。このスキルが決めるのは、実行順序、承認範囲、reviewer との契約、停止条件、完了報告の形式。

## 原則

- **commit は成果物ごとに local で積み、push は最後に 1 回。** 途中で push すると、レビューで直すべき commit がすでに公開されていて取り消せず、修正 commit が上乗せされて履歴が汚れる。
- **修正が効いていなければ、次の修正をせずユーザーに聞く。** 直した finding が再レビューでまだ残っている、修正が新しい blocking を生んだ、同じ invariant への指摘が形を変えて繰り返される。どれも今のアプローチが効いていない証拠で、そこで自動修正を重ねても手戻りが増えるだけ。
- **修正 cycle でやるのは修理であって設計ではない。** レビューの圧力の下で書いた設計は誰もレビューしていない。finding の解消に新しい設計判断が要るなら、修正ではなく仕様の問題として止める。
- **reviewer の重要度は提案であって命令ではない。** 実装側が Requirements と照合して採否を決める。reviewer は計画にない互換性要件や設計上の好みを blocking と呼びがちで、それに従うと要件外の作業が生まれる。
- **仕様か所有権が不確定なら、編集や push の前に止めて聞く。** 推測で進めた分は手戻りになる。

## Authorization

このスキルの起動は次の承認として扱う。

- 検証済みの成果物単位で local atomic commit を作る。
- スコープ内の blocking/high を修正して correction commit を作る。ただし前の修正が効いていなかった場合は、次の修正の前に確認する。
- 全ゲート通過後、Plan archive を含む commit 列を current branch へ 1 回 push する。

force push、amend、rebase、squash、履歴の書き換え、破壊的な削除、要件外の変更、ユーザーや別プロセスの変更、feature branch の作成は承認に含まれない。default branch でも同じゲートを使う。

## Entry modes

ユーザーが選んだ経路を使う。変更規模を理由にエージェントが計画を省略してはならない。

**Plan mode** — 対象 Plan は次の順で決め、複数残るなら確認する。

1. ユーザー指定パス。
2. 現在の会話で作成・選択した Plan。
3. `docs/plans/` 直下に未アーカイブが 1 件だけならそれ。

Plan の Requirements、Implementation Decisions、Out of Scope、Contracts、Testing Decisions、Tasks とその Validation、Final Validation を実装仕様とする。

**Direct mode** — ユーザーが計画を作らず実装すると決めた場合。会話、`dig` の合意、ユーザーの完了条件を実装仕様とする。計画ファイルは作らず、アーカイブもしない。複数領域への波及や新しい設計判断が判明したら停止して `plan` を提案する。

## Preflight

編集前に次を確認する。

1. 対象ファイルに適用される `AGENTS.md` などの指示。
2. Plan 全体、または Direct mode の決定事項と対象外。
3. `git status --short`、`git diff --cached`、`git diff`。ここで見るのは「編集を始めてよいか」だけで、何を stage するかは commit-push が決める。既存の staged 変更があれば開始せず確認する。unstaged/untracked が対象ファイルと重なる場合も確認する。重ならない変更は残し、commit 対象から除外する。
4. upstream、ahead/behind、push 対象範囲。upstream が未設定・曖昧、diverged、開始前から未 push commit がある場合は、それを自分の成果として push しないよう確認する。
5. review 用の base commit を記録する。Plan mode では Plan の Progress に、Direct mode では会話に残し、独立レビューの入力と completion report に使う。

必須 validation が remote CI やデプロイでしか実行できず、Plan やユーザーがその扱いを決めていない場合も、編集前に確認する。

## 成果物ごとの実装

Plan の Task、または Direct mode のレビュー可能な単位ごとに繰り返す。原則 1 Task = 1 commit。大きすぎれば分割、不可分な隣接 Task は統合してよい。

1. 自動テストで観測できる振る舞いは `tdd` を読み、Red → Green を vertical slice ごとに進める。合意済みの test seam は確認済みとして扱い、seam の選択が公開 interface やテスト範囲を変えるなら確認する。文書・設定・生成物には Red を強制せず、構文検査や差分比較など最も近い validation を使う。
2. 同じ context で self-review する。要件対応、scope、明白な欠陥、テスト漏れを見て、必要な refactor はここで行う。独立レビューに refactor を持ち込むと、reviewer が本来見るべき要件適合の確認が薄まる。
3. 成果物に最も近い focused validation を実行する。
4. Plan mode では、変更ファイル、判断に影響する差分、validation 結果だけを該当 Task に反映し、Progress を更新する。Requirement、Out of Scope、Contract はユーザー承認なしに変えない。
5. [`commit-push`](../commit-push/SKILL.md) の **commit-only** で、この成果物、commit-push が doc-updater 経由で更新した文書、Plan 更新だけを local commit する。commit 成功で Task 完了。

Direct mode には Plan の Progress がないので、成果物が複数あって順序や完了状態を追う必要があれば todo を使う。進捗記録だけの文書は作らない。

## 独立レビュー

全成果物を commit した後、Plan や project の標準 validation（test、lint、typecheck、build のうち local で非対話・非破壊に実行できるもの）を実行し、実装由来の residue（一時ファイル、デバッグ出力、未追跡の生成物、commit し漏れた変更）が worktree に残っていないことを確認してから、reviewer に渡す。

独立レビューは Plan mode では必須。Direct mode で省略できるのは、変更がすべて非実行の prose/comment で、契約や運用手順を定義しない場合だけ。事前の validation と residue 確認はどちらのモードでも省略しない。

reviewer の条件:

- 実装を担当していない **read-only の context** を使う。目的は実装側の思い込みから独立した目で見ることで、model や thinking level の差は目的ではないため固定しない。
- re-review は可能なら同じ context を再利用する。再利用できない実行環境（resume 不可、context 消失）では、finding 履歴と correction 範囲を引き継いだ新しい reviewer で続ける。どちらでも再レビューを差分に絞れることが目的で、同一 context 自体は要件ではない。差し替え回数に上限は置かない。reviewer の実行環境の都合は、修正が効いているかどうかとは無関係なため。

reviewer に渡すもの:

- Plan、または Direct mode で確定した Requirements、Contracts、Out of Scope。
- base から HEAD までの diff と commit 一覧。
- 実行した validation とその結果。
- 既存の無関係な worktree 変更。
- 調査範囲はリポジトリ内に限ること。リポジトリ外を調べないと確認できない事項は「未検証」として報告させる。

reviewer には finding を `blocking/high` / `decision required` / `medium/low` / `pre-existing unrelated` に分けさせる。`blocking/high` には、違反する Requirement・Contract・Out of Scope・重大な安全性 invariant、対象箇所、具体的な失敗経路、今回の diff が問題を導入または到達可能にした根拠を必須とする。Requirement が足りず正解を決められない場合は、要件を補わず `decision required` にさせる。

### Triage

- 根拠を満たすスコープ内の `blocking/high` は採用し、同一レビューで出た分をまとめて修正する。
- 採用した finding でも、解消に Plan の Implementation Decisions（Direct mode では合意済みの設計）にない要素の追加や、既存 decision の実現方法の変更が必要なら、修正せず `decision required` として扱う。この判断は修正に着手する前に行う。
- 根拠不足、未合意の互換性・将来要件、設計上の好みは採用せず、理由を記録する。
- `decision required` は修正前に停止し、1 件ずつ確認する。
- `medium/low` は修正せず completion report に残す。
- `pre-existing unrelated` は報告のみ。ただし今回の diff が悪化させた、または到達可能にしたものは今回の finding として扱う。

reviewer 出力が証拠形式を満たさなければ、1 度だけ補足を求める。補足後も満たさなければ停止する（「停止して確認する条件」参照）。

## 修正 cycle

1 cycle は、採用した `blocking/high` をまとめて修正 → 影響範囲の validation → local correction commit → scoped re-review、の一巡。scoped re-review の対象は、既存 finding の解消、correction diff、その修正が直接影響する経路に限る。

修正は Plan の Implementation Decisions の範囲内で行う。範囲を出る finding は Triage の時点で `decision required` になっているはずで、修正の途中で範囲を出ることが分かった場合も、その cycle を打ち切って同じ扱いにする。

scoped re-review が「対象 finding はすべて解消、新しい `blocking/high` なし」を返したら final validation へ進む。次のどれかに当たる場合は、次の修正を自動で始めず停止する。

- 直した finding が解消されていない。
- correction diff が新しい `blocking/high` を生んだ。
- 一度修正した invariant に対する指摘が、別の経路や入力で繰り返されている。

停止時は、未解決 finding、根拠、対応案を示す。対応案には、同じアプローチで修正を続ける案のほかに、Requirement や受け入れ範囲を狭める案を必ず含める。修正が効かなかったという事実自体がアプローチの問題を示しているので、選択肢を修正継続だけにしない。

ユーザーが修正の続行を選んだ場合は、その指示の範囲で 1 cycle 行い、同じ判定に戻る。ユーザーが Requirement や Contract の変更を承認した場合は、Plan または合意を更新して影響範囲を実装・validation し、新仕様に対する full review を行う。`decision required` の解消は仕様の確定であって変更ではないので、full review はせず、確定した内容を Plan または合意に反映して続ける。

## Final validation と delivery

`blocking/high` と `decision required` がなくなったら final validation を行う。

- review 前に成功した validation のうち、入力と対象挙動が変わっていないものは再利用する。
- 外部環境・手動確認が必要なもの、変更で無効になったものだけを実行する。
- ここで substantive fix が必要になれば、修正 cycle として扱い、同じ停止条件を適用する。

full suite の失敗が base でも再現し無関係と確認できても、自動修正、N/A 化、成功扱いはしない。どれも実装側が受入条件を勝手に緩めることになるため、受入条件を変えるかどうかをユーザーに確認する。

review と validation が同じ HEAD に対して有効になったら:

1. Plan mode では、review 対象 commit、採用した finding と correction commit、未解決なしの旨を gate summary として Plan に書き、同名のまま `docs/plans/archived/` へ移す。移動と summary を **1 つの archive commit** にまとめる（commit-push の commit-only を使う）。archive 後に管理用 commit を追加しない。
2. `git status --short`、`git diff --cached`、`git diff` を再確認する。実装由来の residue があれば validation と review へ戻る。
3. Preflight の push 範囲と upstream を再確認し、通常の `git push` で commit 列全体を 1 回 push する。

push 成功まで完了扱いにしない。push が失敗しても local commit は戻さず、エラーと再実行条件を報告する。

## 停止して確認する条件

- Requirement、Contract、Out of Scope、合意済み test seam の変更が必要になった。
- `decision required` が出た。finding の解消に Plan の Implementation Decisions 外の設計判断が必要な場合を含む。
- 修正が効いていない（直した finding が解消されない、修正が新しい `blocking/high` を生む、同じ invariant への指摘が繰り返される）。
- reviewer 出力が補足後も証拠形式を満たさない。
- 所有権が衝突する（既存 staged、対象と重なる unstaged、開始前の未 push commit、曖昧な upstream）。
- 受入条件を満たせない validation 失敗が残った。

停止時は未完成の変更を push せず、未 commit の変更は local に残す。Plan mode では、失敗した validation、判明した原因、未完了の範囲、再開に必要な判断を Plan に記録する。

## Completion report

1. 完了または未完了の結論。
2. 実装した成果物と主要 commit。
3. validation 結果（実行・再利用・未実行）。
4. 独立レビュー、採用した finding、修正 cycle の経過、残した medium/low。
5. Plan mode では archive 先。Direct mode では Plan なしで完了した旨。
6. push 結果。
7. 残した無関係な worktree 変更または未解決 blocker。
