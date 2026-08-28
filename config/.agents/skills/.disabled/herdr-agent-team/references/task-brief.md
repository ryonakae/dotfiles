# Task briefのtemplate

Main Piはworkerを起動した後、assignmentを最初のuser messageとして送る。会話履歴は貼らず、workerがそれだけで着手できる事実を書く。

## 必須項目

```markdown
# Assignment

## Task
<達成すべき成果を一つ>

## Mode
Plan | Direct

## Role
<researcher | implementer | reviewer | tester | debugger | documenter | custom>

## Permission
read-only | writer

## 正本
- Repository root: <absolute path>
- Plan: <absolute path または None>
- Task ID: <PlanのTask ID、またはDirectの成果物ID>
- 有効なworkflow: <implement/tddなど、なければNone>

## Baseline
- HEAD: <sha>
- Branch/upstream: <値>
- 既存のstaged変更: <path、なければNone>
- 既存のunstaged/untracked変更: <pathと所有者>
- Writer owner: <agent名 | Main Pi | None>
- Read-only開始baseline: <HEAD/index/worktreeのsnapshot | N/A>
- Active/accepted writer delta ledger: <writer、lease期間、許可path、状態、Main Piが検証したcommit/diff | None>

## 検収済みの根拠
- <Main Piが既に確認した事実>

## Scope
- 対象: <file、挙動、問い>
- 対象外: <境界>
- 依存: <検収済みのTask ID、なければNone>

## Validation
- 必須: <commandまたは確認内容>
- 実行しない: <危険なもの、対話が必要なもの、Main Piが担当するもの>

## 完了条件
Worker共通contractが定める固定reportを返す。このbriefがPlan、repositoryの指示、permission contract、現在のbaselineと矛盾する場合は、作業を止めてBlockedを報告する。
```

## Plan mode

Plan modeではPlanのabsolute pathとTask IDを必須にする。workerには作業前にPlan全体を読ませる。briefはPlanを要約して置き換えるものではなく、role、permission、baseline、検収済みの根拠、focused validationだけを補う。

`/implement`が有効なwriter assignmentには次を明記する。

- 担当Taskのfileだけを編集する。
- Taskの変更内容、判断に影響した差分、validation、ProgressをPlanへ反映する。
- focused validationの後、担当成果物とPlan更新をcommit-onlyで一つのatomic commitにまとめる。
- push、archive、全体のreview triageはMain Piが担当する。

reviewer assignmentには、reviewの起点、対象commitの並び、validationの結果、findingの分類と根拠の書式を指定する。reviewerのpermissionは`read-only`に固定する。

## Direct mode

Direct modeでは成果物ID、完了条件、commit方針を明記する。通常のteam taskは、ユーザーがcommitを求めない限り`Commit: None`とする。

既存の変更がある場合は、path、状態、所有者をBaselineへ書く。対象と重なる変更の意図が不明ならworkerを起動しない。

read-only workerをwriterと並行させる場合は、そのworker固有の開始baselineと、active/accepted writer delta ledgerを必須にする。read-onlyの開始後にwriterを追加する場合も、dispatchの前にledgerへ追記する。Main Piが同時点の終了状態から検証したcommit/diffだけをledgerへ反映し、帰属が曖昧ならread-onlyの成果を受理しない。

## Custom role

custom role用に一時的なsystem prompt fileを作らない。`Role`には短い名前を書き、`Task`と`Scope`で責務を定義する。common contractとpermission contractはbuilt-in roleと同じように付ける。

## Correction brief

同じworkerへ差し戻すときは、元のassignmentを再送せず差分だけを示す。

```markdown
# Correction

## 検収済み
<既に確認済みで変更が不要な内容>

## Blockingな不足
- 違反している要件またはcontract: <出典>
- 根拠: <diff、report、validation>
- 必要な修正: <範囲を限定した変更>

## Validation
<再実行が必要なもの>

元のrole、permission、担当範囲、baselineの保持、reportの形式はそのまま維持する。担当範囲を広げない。
```

re-reviewのbriefも同じ形式で、既存findingの解消、correctionのdiff、その影響経路だけを対象にする。

## Blocked時の応答

workerがblockedになった場合、Main Piは次のように分類する。

- 既存の依頼、Plan、repositoryから一意に決まる: Main Piが根拠を付けて回答する。
- 仕様の選択、権限、機密情報、破壊的操作: ユーザーへ一度に一つ確認する。
- Safehouse拒否: command、目的、想定時間を確認し、ユーザーの承認前はhost shellで実行しない。

blocked UIへの入力方法はHerdr Skillを正本とする。通常のpromptを重ねて押し切らない。
