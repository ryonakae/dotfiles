---
name: implement
description: 確定した要件を実装、検証、atomic commit、push、独立レビュー、必要な計画アーカイブまで完遂する。計画があれば Plan mode、ユーザーが計画を省略して直接実装すると決めた場合は Direct mode で進める。
compatibility: Gitリポジトリと、tdd・commit-pushスキル、独立したreviewerを起動できる実行環境を前提とする。
disable-model-invocation: true
---

# Implement

確定した要件を、検証と独立レビューを通った状態でremoteへ反映する。テスト品質は`tdd`、staging、commit、文書更新は[`commit-push`](../commit-push/SKILL.md)を正本とする。このスキルは実行順序、reviewerとの契約、完了条件を管理する。

## Authorization

このスキルの起動を、次の承認として扱う。

- 検証済みの成果物単位でlocal atomic commitを作る。
- スコープ内のblocking/highを、定めた予算内で修正してlocal atomic commitを作る。
- 全ゲート通過後、Plan archiveを含むcommit列をcurrent branchへ一度pushする。

成果物ごとのpush、force push、rebase、amend、squash、履歴の書き換え、破壊的な削除、要件外の変更、ユーザーや別プロセスの変更は承認に含まれない。default branchも同じゲートを使う。feature branchの作成や推奨は行わない。

Planまたはユーザーがremote-only validation用のpush先と公開条件を決めた場合だけ、その合意を通常の一回pushに対する例外として使う。

## Entry modes

ユーザーが選んだ経路を使う。エージェントが変更規模を理由に計画を省略してはならない。

### Plan mode

次の順で対象プランを決める。

1. ユーザーが指定したパス。
2. 現在の会話で作成または選択したプラン。
3. `docs/plans/`直下にある未アーカイブの計画が1件だけなら、その計画。

複数候補が残る場合は、編集前に対象を一つ確認する。PlanのRequirements、Decisions、Out of Scope、Contracts、Tasks、Validationを実装仕様とする。

### Direct mode

ユーザーが計画を作らず実装すると決めた場合に使う。現在の会話、`dig`で合意した決定、ユーザーが提示した完了条件を実装仕様とする。計画ファイルは作成せず、アーカイブもしない。

要件、Out of Scope、公開契約、永続形式、テスト境界に未確定事項が残る場合は、実装を始めず一度に一つ確認する。複数領域への波及や新しい設計判断が判明し、直接実装の前提が崩れた場合は停止して`plan`を提案する。

## Preflight

編集前に次を行う。

1. 対象ファイルへ適用される`AGENTS.md`などの指示を読む。
2. Plan modeではPlan全体を読み、Direct modeでは決定事項と対象外を整理する。
3. `git status --short`、`git diff --cached`、`git diff`でstaged、unstaged、untrackedを確認する。
4. upstream、ahead/behind、push対象commit rangeを確認する。upstreamが未設定または曖昧、branchがdiverged、開始前から未push commitがある場合は、所有権を推測せず編集前に確認する。
5. この実装が所有する変更パスと、開始前から存在する変更パスを区別する。
6. 既存のstaged変更がある場合は、所有権が明確でも開始せず確認する。
7. 既存のunstaged/untracked変更が対象ファイルと重なる場合は開始せず確認する。重ならない変更は残し、commit対象から除外する。
8. review用のbase commitを記録する。
9. 成果物の数と依存関係を確認し、必要な場合だけユーザー可視のtodoを作る。

PlanやDirect modeの変更が公開契約、永続形式、互換性へ影響するのに方針が決まっていない場合は停止する。release、tag、branch、途中commitから互換性要件を推定しない。

必須validationがremote CIやpreview deployでしか実行できない場合は、Planまたはユーザーがpush先、公開条件、途中反映の扱いを決めているか確認する。未決定なら編集前に停止する。

## TDD and local delivery

自動テストで観測できる振る舞いには`tdd`スキルを読み、確定済みのtest seamでRed → Greenを繰り返す。

- PlanのTesting Decisionsまたは`dig`で合意したseamは確認済みとして扱う。
- seamが未決定で、選択によって公開interfaceやテスト範囲が変わる場合は確認する。
- 一つの振る舞いについて、失敗するテストを確認してから、それを通す最小限の実装を書く。
- 先のテストや機能をまとめず、vertical sliceごとに進める。

文書、設定、生成物など、失敗テストを作る意味がない変更にはRedを強制しない。Plan modeでは理由と代替validationを該当Taskへ記録する。Direct modeでは進捗報告に示し、構文検査、差分比較、実command確認など最も近いvalidationを使う。

成果物ごとに次を行う。

1. 対象成果物をin progressにする。
2. TDDまたは合意済みの代替validationで実装する。
3. 同じ実装contextでtask-level self-reviewを行う。要件対応、scope、明白な欠陥、テスト漏れを確認し、必要なrefactorをここで行う。
4. 成果物に最も近いfocused validationを実行する。self-reviewで変更した場合は、その変更を含む状態で実行する。
5. Plan modeでは、実際の変更ファイル、軽微な実装差分、validation結果を該当Taskへ反映し、Progressを完了へ更新する。Requirement、Out of Scope、Contractはユーザー承認前に変えない。
6. [`commit-push`](../commit-push/SKILL.md)を読み、この成果物とPlan更新だけを**commit-only**で処理する。pushしない。
7. local commitが成功した時点でTaskの完了を確定する。commitが失敗した場合は完了扱いにせず、Plan更新をlocalに残す。

原則は1 Plan Taskにつき1commitとする。Taskが一つのreview/revert単位として大きすぎる場合は分割し、小さく不可分な隣接Taskは統合できる。Plan modeではcommitとの対応を記録する。Direct modeでは作業テーマ単位で分ける。

Task-level reviewは同じ実装contextで行う。独立reviewerによる中間checkpointは、Planまたはユーザーが明示した場合だけ実行する。そのcheckpointは後述の一つのreviewer contextと共通の修正予算を使う。

## Progress

### Plan mode

- focused validation、self-review、Plan更新、local commitが成功したら、Progressの対応項目を完了にする。
- 後のreview findingがTaskに関係する場合は再びin progressへ戻し、correction commitとvalidation後に完了へ戻す。
- 計画との差異は作業ログとして羅列せず、変更ファイル、判断に影響する差分、validation結果だけを残す。
- Final Validationは実行して成功した項目だけを完了にする。

### Direct mode

- 3件以上の意味ある成果物や依存関係がある場合はtodoを使う。
- 小さな変更ではチャットの進捗だけを使う。
- Git履歴を実装記録とし、進捗記録だけの文書は作らない。

進捗報告は経過時間ではなく状態変化に合わせる。初回reviewでblocking/high修正へ入るときは報告して自走を続ける。Requirement、Contract、Out of Scope、合意済みtest seamの変更、`decision required`、review予算枯渇、reviewer利用不能、所有権衝突、受入条件未達では停止して確認する。

## Review readiness

全成果物をlocal commitした後、reviewerへ渡す前に次を行う。

1. Taskのfocused validation結果を確認する。
2. Planまたはprojectで標準化された、localで非対話、非破壊に実行できるtest、lint、typecheck、buildを実行する。
3. 外部環境、資格情報、実deploy、手動操作が必要なvalidationはfinal validationへ残す。
4. `git status --short`、`git diff --cached`、`git diff`を確認する。実装所有のsubstantive residueがあれば、必要なvalidationとlocal commitを行う。
5. review対象HEAD、baseからのcommit一覧、実行済みvalidationと結果を記録する。

Planまたはユーザーが一時的なreview evidenceを明示している場合は、commit対象外としてreview完了まで残せる。所有者、path、cleanup条件が明確でなければ、この例外を使わない。

## Independent review

Plan modeでは必須とする。Direct modeで省略できるのは、変更のすべてが非実行のprose/commentで、Contractや運用手順を定義しない場合だけとする。code、test、script、dependency、build/CI、挙動に影響する設定はreviewする。

実装を担当していない一つのread-only reviewer contextを使う。Planで明示した中間checkpoint、final full review、scoped re-reviewで同じcontextを継続する。中間checkpointを通過していても、final reviewはbaseから完成HEADまでの全実装範囲を確認する。model名やthinking levelは固定しない。

reviewerへ次を渡す。

- Plan modeのPlan、またはDirect modeで確定したRequirements、Contracts、Out of Scope。
- base commitからreview対象HEADまでの実装diffとcommit一覧。
- 実行したvalidation、その結果、結果が対応するHEAD。
- 既存の無関係なworktree変更と、明示された一時review evidence。
- 初回は全実装範囲、再reviewは後述の限定scope。

reviewerはsourceを編集、commit、validation結果の書き換えを行わない。成功済みfull suiteを独立性のためだけに再実行せず、findingの再現または未検証経路の確認に必要なfocused commandだけを実行できる。

### Reviewer output contract

findingを次のcategoryに分ける。

- `blocking/high`
- `decision required`
- `medium/low`
- `pre-existing unrelated`

各`blocking/high`には次を必須とする。

- 違反するRequirement、Contract、Out of Scope、合意済みDecision、または重大な安全性invariant。
- 対象箇所。
- 具体的な入力、実行経路、失敗結果、または静的に追跡できるfailure path。
- 今回のdiffが問題を導入、悪化、到達可能にした根拠。
- severityの理由。

今回と無関係な既存問題は`pre-existing unrelated`へ分ける。未合意の将来要件、互換性、設計上の好みを`blocking/high`にしない。RequirementやContractが不足して正解を決められない場合は、要件を補わず`decision required`とする。

## Finding triage

reviewerのseverityをそのまま実装命令にしない。実装担当がfindingをRequirementsと上記証拠形式へ照合する。

- 根拠を満たすscope内の`blocking/high`は採用し、同じreviewer generationのfindingをまとめて修正する。
- 根拠不足、将来改善、設計上の好みはblocking対象から外し、理由を記録する。
- `decision required`は修正前に停止し、ユーザーへ一つずつ確認する。
- `medium/low`は今回中に修正せず、completion reportへ残す。
- 今回のdiffが導入、悪化、到達可能にしていない`pre-existing unrelated`は報告するが、deliveryを止めない。

既存問題でも、今回のdiffが新たに到達可能にした、悪化させた、またはRequirement達成を妨げる場合は今回のfindingとして扱う。

reviewer出力が証拠形式を満たさない場合は、同じcontextへ一度だけ補足を求める。context/tool障害では代替reviewerを一度だけ使い、Plan、finding履歴、限定scopeを引き継ぐ。有効な独立reviewを得られなければ未完了で停止する。これはcorrection cycleに数えない。

## Correction budget and scoped re-review

一回の`implement` invocation全体で、自動correction cycleを最大2回とする。中間checkpoint、final review、final validation起因のsubstantive fixを合算する。

1 cycleは次のまとまりとする。

1. 一つのreviewer generationで採用した`blocking/high`をtriageしてまとめる。
2. TDDまたは同等のvalidation規則で修正する。
3. 一つ以上のlocal atomic correction commitを作る。amend、rebase、squashは行わない。
4. 影響範囲のvalidationを実行する。
5. 同じreviewerへscoped re-reviewを依頼する。

scoped re-reviewの対象は、既存findingの解消、correction diff、その修正が直接影響する実行経路に限る。correctionが導入または顕在化した新しい`blocking/high`は次cycleで扱える。初回実装diffに元から存在し、scoped re-reviewで初めて見つかった有効なHighは自動修正せず、根拠と選択肢を示してpush前に停止する。

2 cycle終了時に`blocking/high`が残る場合は、明白な小修正でも3 cycle目へ進まない。未解決finding、根拠、対応案を示して停止する。

ユーザーがRequirementまたはContract変更を承認した場合は、PlanまたはDirect modeの合意を更新し、影響範囲を実装、validationした後、新仕様に対するfull reviewを行う。新しい2-cycle budgetを使う。変更がPlanの前提を崩す場合は停止して新しいPlanを提案する。

## Final validation and delivery

独立reviewで未解決の`blocking/high`と`decision required`がなくなった後、final validationを行う。

- review前validationの入力と対象挙動が変わっていなければ、その成功結果を再利用する。
- 未実行の外部/manual項目と、変更によって無効化されたvalidationだけを実行する。
- 再利用可否が曖昧なら、影響するvalidationを安全側で再実行する。全commandを一律に繰り返さない。
- final validationがsubstantive fixを必要とした場合はlocal correction commitを作り、correction budgetを1 cycle使って影響validationとscoped re-reviewを行う。

full suiteの失敗がbaseでも再現し、今回と無関係だと確認できても、自動修正、`N/A`化、成功扱いはしない。根拠とscope内validationの成功を示し、受入条件を変えるかユーザーへ確認する。解決までPlanをarchiveせず、完了を主張しない。

reviewとvalidationが同じimplementation HEADに対して有効になったら、次の順でdeliveryする。

1. Plan modeでは、review対象commit、採用した`blocking/high`とcorrection commit、未解決`blocking/high`がないことを最小限のgate summaryとして記録する。
2. 明示された一時review evidenceを、所有権とpathを確認して削除する。
3. `git status --short`、`git diff --cached`、`git diff`を再確認する。
4. implementation-ownedなsubstantive residueがあれば、必要なlocal commit、validation、scoped re-reviewへ戻る。
5. Plan modeではPlan archive条件を確認し、同名のまま`docs/plans/archived/`へ移して独立したlocal commitを作る。archive commitにも[`commit-push`](../commit-push/SKILL.md)のcommit-only手順を使う。
6. archive準備や文書更新がPlan管理以外のsubstantive変更を生んだ場合は、archive commitへ混ぜず、validationとreviewへ戻す。
7. Preflightで確認したpush rangeとcurrent upstreamを再確認し、通常の`git push`でcommit列全体を一度pushする。

push成功まで完了扱いにしない。pushが失敗した場合はlocal commitを戻さず、エラーと再実行条件を報告する。remote更新が必要なmerge、rebase、force pushは自動で行わない。

## Plan archive

Plan modeだけで行う。次の条件をすべて満たしてからarchiveする。

- すべてのTaskと、Plan archive自体を除くFinal Validationが完了している。
- Requirement Coverageと実際の変更が一致している。
- validationと独立reviewが同じimplementation HEADに対して有効である。
- 未解決の`blocking/high`と`decision required`がない。
- correction後のvalidationとscoped re-reviewが完了している。
- implementation-ownedなsubstantive residueがない。
- final push対象のcommit列とupstreamが確定している。

archive移動とgate summaryは管理上の変更としてcode re-review対象から除外する。archive前に条件を満たせなくなった場合は、Planを未アーカイブの場所へ残す。

## Blockers

validation失敗、所有権衝突、未確定仕様、reviewer利用不能、review予算枯渇などのblockerが残った場合は、未完成の変更をpushしない。未commitの変更はlocalに残し、Plan modeでは次を記録する。

- 失敗したvalidationと結果。
- 判明した原因。
- 未完了の範囲。
- 再開に必要な判断または条件。

pushだけが失敗した場合は、作成済みlocal commitを戻さない。push成功までPlan archive後の状態を含めて未配信として扱い、完了を主張しない。

## Completion report

次の順で簡潔にまとめる。

1. 完了または未完了の結論。
2. 実装した成果物と主要commit。
3. 実行、再利用、未実行に分けたvalidation結果。
4. 独立review、採用したfinding、correction cycle数、残したmedium/low。
5. Plan modeではarchive先。Direct modeではPlanなしで完了した旨。
6. final push結果。
7. 残した無関係なworktree変更または未解決blocker。
