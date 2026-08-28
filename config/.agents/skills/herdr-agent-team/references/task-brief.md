# Task brief templates

Main Piはworker起動後、assignmentを最初のuser messageとして送る。会話履歴を貼らず、workerが単独で開始できる事実だけを書く。

## Required fields

```markdown
# Assignment

## Task
<one bounded outcome>

## Mode
Plan | Direct

## Role
<researcher | implementer | reviewer | tester | debugger | documenter | custom>

## Permission
read-only | writer

## Source of truth
- Repository root: <absolute path>
- Plan: <absolute path or None>
- Task ID: <Plan Task ID or Direct outcome ID>
- Active workflow: <implement/tdd/etc. or None>

## Baseline
- HEAD: <sha>
- Branch/upstream: <value>
- Existing staged changes: <paths or None>
- Existing unstaged/untracked changes: <paths and ownership>
- Writer owner: <agent name | Main Pi | None>
- Read-only start baseline: <HEAD/index/worktree snapshot | N/A>
- Active/accepted writer delta ledger: <writer, lease interval, allowed paths, state, Main-verified commit/diff | None>

## Accepted evidence
- <facts already verified by Main Pi>

## Scope
- In scope: <files/behavior/questions>
- Out of scope: <boundaries>
- Dependencies: <accepted Task IDs or None>

## Validation
- Required: <commands/checks>
- Do not run: <unsafe, interactive, or Main-owned commands>

## Completion
Return the fixed report required by the common worker contract. Stop and report Blocked if this brief conflicts with the Plan, repository instructions, permission contract, or current baseline.
```

## Plan mode

Plan modeではPlanのabsolute pathとTask IDを必須にする。workerへ作業前にPlan全体を読ませる。briefはPlanを要約して置き換えず、role、permission、baseline、検収済みevidence、focused validationだけを補う。

`/implement`が有効なwriter assignmentには次を明記する。

- 担当Taskのfileだけを編集する。
- Taskの変更内容、判断に影響した差分、validation、ProgressをPlanへ反映する。
- focused validation後、担当成果物とPlan更新をcommit-onlyで一つのatomic commitにする。
- push、archive、全体review triageはMain Piが担当する。

reviewer assignmentにはreview base、対象commit列、validation結果、finding分類と証拠形式を指定する。reviewer permissionは`read-only`に固定する。

## Direct mode

Direct modeでは成果物ID、完了条件、commit方針を明記する。通常team taskは、ユーザーがcommitを求めない限り`Commit: None`とする。

既存変更がある場合はpath、状態、所有者をbaselineへ書く。対象と重なる変更の意図が不明ならworkerを起動しない。

read-only workerをwriterと並行させる場合は、そのworker固有の開始baselineと、active/accepted writer delta ledgerを必須にする。read-only開始後にwriterを追加する場合もdispatch前にledgerへ追記する。Main Piが同時点の終了状態から検証したcommit/diffだけをledgerへ反映し、帰属が曖昧ならread-only成果を受理しない。

## Custom role

custom role用の一時system prompt fileは作らない。`Role`に短い名前を書き、`Task`と`Scope`で責務を定義する。common contractとpermission contractはbuilt-in roleと同じように付ける。

## Correction brief

同じworkerへ返すときは、元のassignmentを再送せず差分だけを示す。

```markdown
# Correction

## Accepted
<既に検収済みで変更不要な内容>

## Blocking gap
- Requirement/contract: <source>
- Evidence: <diff, report, validation>
- Required correction: <bounded change>

## Validation
<rerun required>

Keep the original role, permission, scope, baseline-preservation, and report contract. Do not broaden the task.
```

re-review briefも同じ形式で、既存findingの解消、correction diff、その影響経路だけを対象にする。

## Blocked response

workerがblockedの場合、Main Piは次を分類する。

- 既存依頼、Plan、repositoryから一意に決まる：Main Piが根拠付きで回答する。
- 仕様選択、権限、機密情報、破壊的操作：ユーザーへ一度に一つ確認する。
- Safehouse拒否：command、目的、想定時間を確認し、ユーザー承認前はhost shellで実行しない。

blocked UIへの入力方法はHerdr Skillを正本とする。通常promptを重ねて押し切らない。
