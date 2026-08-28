# Herdr Agent Team Skill Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

Piの通常のsubagent委譲はMain Piのturnを待機させ、Herdr UIにも独立した作業主体として表示されない。Herdrでは複数の対話agentとshellをpaneへ配置でき、Shepherdは同一workspace内のagent履歴・状態・完了outcomeをMain Piへ集約できるが、タスク分解、単一writer、命名、タブ構成、モデル選択、Plan/Implement連携、レビュー、失敗時処理を一貫して運用するteam workflowは存在しない。

新しいSkillはHerdrやShepherdの操作・観測機能を再実装せず、Main Piを唯一のユーザー対話窓口かつShepherd ownerとして、必要なPi workerを同一workspace内へjust-in-timeに起動・指示・検収する実行方針を提供する必要がある。

## Goal

`herdr-agent-team` Skillを作成し、ユーザーがHerdr上で可視化されたagent teamを明示的に求めた場合に、Main Piが次を一貫して行えるようにする。

- `orchestrator`、`agents`、`shells`の予約タブを安全に作成・再利用する。
- task、role、permission、provider、model、thinkingを分離し、既存Pi routing policyから起動構成を選ぶ。
- 同一checkout・最大4 worker・同時1 writerの範囲で、dependency-readyなworkerだけを非同期起動する。
- Shepherd wakeを完了契機として使い、構造化履歴、実diff、validationを確認してから次工程へ進む。
- Plan modeと`/implement`の既存契約を正本として、Herdr上のimplementerと独立reviewerへ作業を割り当てる。
- Skill Creatorのpaired evaluationと人間のreviewを通じて、通常のHerdr操作、owner境界、Safehouse、review、worktree対象外などの判断を検証する。

## Out of Scope

- Shepherd本体、`shepherd-pi`、Shepherd Agent Skill、Shepherd Herdr pluginのインストール・更新・設定変更。
- 既存の`herdr`、Shepherd、`implement`、`plan`、`commit-push`、`use-worktrunk`、`use-agent-safehouse` Skillの変更。
- `config/.pi/agent/settings.json`、`config/.pi/agent/agent-tool-description.md`、Pi extension、Herdr plugin/config、本リポジトリのSafehouse policyの変更。
- Claude CodeなどPi以外のworker provider、provider adapter、料金・rate-limit routerの実装。
- worktreeの作成・切替・workspace登録、複数writerの同時実行、branch作成。
- 独自daemon、task DB、mailbox、event cursor、polling loop、watchdog、shell完了通知hook、Pi sessionの`/new`後の復旧機構。
- read-only worker専用のOS-level sandboxやfilesystem copy。
- Herdr/Shepherd内部RPCやSQLiteへの直接アクセス、`/shepherd on`の自動実行・owner自動選出。
- Herdr/Shepherdの実環境を変更する自動integration eval。今回のShepherd依存は未導入のため、状態判断はfixtureベースで評価する。
- Skill Creatorのiteration workspace、transcript、timing、grading、benchmark、viewer、feedbackのGit管理。
- Skill CreatorのClaude CLI専用description optimization loop。対象runtimeはPi/OpenAIであり、Claude CLIのtrigger結果をPiのtrigger品質として採用しない。

## Requirements and Decisions

### Requirements

- **R1:** Skill名は`herdr-agent-team`とし、Herdr、agent team、複数agent、可視化された並行作業をユーザーが明示した場合だけtriggerする。通常の単一agent実装や`/implement`だけでは自動triggerしない。
- **R2:** compatibilityは、Git repository、`HERDR_ENV=1`、利用可能なHerdr CLI、Shepherd daemon/Agent Skill、`shepherd-pi`、Main Piで事前に有効化されたShepherd ownerを要求する。Shepherd Herdr pluginは推奨だが任意とする。
- **R3:** workspace内に`orchestrator`、`agents`、`shells`の予約タブを維持する。Main Piの現在tab/paneを`orchestrator`として扱い、別paneが同居していれば自動移動・終了せず開始を止める。無関係な既存tabは残す。
- **R4:** `agents`と`shells`はteam専用予約tabであり、内部paneは名前にかかわらずteam管理対象とする。同名tabが曖昧、または`orchestrator`名が別tabと衝突する場合は、連番や推測で続行せず停止する。
- **R5:** pane layoutは、1 pane全面、2 pane左右、3 pane左1・右上下2、4 pane 2×2とする。作成・再配置でfocusを奪わず、Main Piまたはユーザーが現在選択しているfocusを勝手に変更しない。
- **R6:** agentとshellの初期cwdはGit repository rootとする。monorepoの特定packageなど明確な理由がtask briefにある場合だけ例外cwdを指定する。
- **R7:** workerは最大4体とし、dependency-readyなtaskだけをjust-in-timeで起動する。依存先が未完了のimplementer/reviewerを待機目的で先行起動しない。空きが必要なら、Main Piが成果を取得・検収済みの完了paneだけを閉じてfresh workerへ置き換える。
- **R8:** 基本roleは`researcher`、`implementer`、`reviewer`、`tester`、`debugger`、`documenter`とし、Main Piは任意roleもその場で追加できる。pane/agent名は`<actor-role>-<task-slug>[-N]`形式で、`[a-z][a-z0-9_-]{0,31}`へ収め、一意化する。
- **R9:** roleとpermissionを分離し、各task briefへ`read-only`または`writer`を明記する。同一checkoutでは全role合計で同時writerを1体だけとし、通常はimplementerが所有する。Main Piが編集を引き取る場合はworkerを停止または待機させてからownershipを移す。
- **R10:** read-only制約はsystem-level worker contractで指示し、Main Piが開始baselineと終了diffを検査する。専用sandboxは作らず、違反時は成果を受理せず、変更を自動で戻さない。
- **R11:** V1のworker providerはPiだけとする。Main Piはworker起動ごとに`$HOME/.pi/agent/agent-tool-description.md`を正本としてmodelとthinkingを独立選択し、そのrouting表・model ID・benchmarkをSkillへ複製しない。起動失敗は理由にかかわらず自動再試行しない。
- **R12:** Main Piと全workerはteam mode中にPiの`Agent` subagentを起動しない。worker間の直接promptも行わず、追加調査、結果、質問、再指示はMain Piを経由する。各agentの通常のshell tool利用は制限しない。
- **R13:** Pi worker起動時は、共通contract、permission contract、基本role contractを`herdr agent start ... -- --append-system-prompt <file>`でsystem promptへ追加する。Plan/task briefは`herdr agent prompt`の最初のuser messageとして`--wait`なしで送る。任意roleは共通contractとpermissionを維持し、目的だけをtask briefで補う。
- **R14:** 共通worker contractは、適用される`AGENTS.md`等の遵守、Main Piから割り当てられた範囲、subagent禁止、peer communication禁止、permission、ユーザー変更の保持、worktree禁止、Safehouse境界、固定最終報告形式を定める。
- **R15:** workerの最終報告はMarkdownの`Result`、`Changed`、`Validation`、`Commit`、`Remaining`を固定項目とし、該当なしは`None`とする。blocked/failedの場合も、必要な判断、command、根拠を同形式で返す。
- **R16:** Plan modeではworkerへ計画ファイルpathと担当Task IDを渡し、作業前にPlan全体を読ませる。task briefはrole、permission、baseline、担当Task、直近の検収済み調査、報告形式だけを補足し、Planと矛盾したら停止させる。
- **R17:** Planの担当Taskに関する変更内容・validation・Progressはimplementerがコードと同じ成果物commitへ含める。全Taskとreview完了後にwriter ownershipをMain Piへ移し、Main Piがgate summaryとarchive commitを担当する。
- **R18:** `/implement`が明示的に有効な場合は、そのAuthorization、preflight、atomic commit、最大2 correction cycle、review、archive、final push、停止条件を正本とする。Main Piがworkflowを管理し、Herdr implementerは個別成果物の編集・focused validation・commit-only、Herdr reviewerはread-only reviewを担当する。既存`implement` Skillは変更しない。
- **R19:** `/implement`が有効でないteam taskでは、明示依頼がない限りcommitしない。開始時の`git status`、staged/unstaged/untracked差分をbaselineとして記録し、既存変更を保持する。対象と重なる変更の意図が不明なら編集前に確認する。
- **R20:** コード、設定、scriptを変更した通常team taskにはfresh reviewerを必須とする。`/implement`利用時のreview免除・finding分類・最大cycleは`implement`を正本とする。それ以外では仕様違反、正確性、回帰、security、data loss、必要test不足をblockingとし、medium/lowは報告のみとする。
- **R21:** 初回reviewはfresh read-only Herdr reviewerを使い、re-reviewは同じcontextで行う。team modeでは通常subagent reviewerへ自動fallbackしない。通常team taskで同一blockerが修正後も残る場合は、既存routing ruleに従ってfresh implementerへ一度escalateし、それでも解消しなければユーザーへ戻す。
- **R22:** writerと独立したread-only調査は並行可能だが、writerの変更に依存する調査とreviewは安定したdiff/commitができるまで起動しない。複数writer要求は直列化し、同時実行そのものが要件ならV1非対応として停止する。
- **R23:** Shepherd daemonが停止中なら自動起動し、失敗時はworkerを起動しない。Main Piの`/shepherd on`はユーザー管理の事前条件として扱い、Skillからownerを自動claimまたは内部照会しない。
- **R24:** Shepherd wakeは完了検知にのみ使い、受理前に対象agentへ`shepherd agent get`を実行する。truncated、詳細不足、矛盾がある場合だけ`read`またはHerdr terminalを確認する。writer成果はさらに実diffとvalidationを確認する。
- **R25:** workerが`blocked`になったら、既存依頼・Plan・repositoryから一意に解決できる内容はMain Piが続行する。仕様選択、権限承認、機密情報、破壊的操作はユーザーへ確認する。blocked agentのUI応答はHerdr skillの正規操作に従い、通常promptで押し切らない。
- **R26:** ownerを実行中に失った場合、既存workerは止めず、新規起動・再指示を停止する。ユーザーへowner復旧を求め、復旧後にShepherd履歴から状態を再同期する。異常終了用の追加polling/watchdogは作らず、次の通常turnで消失・`unknown`を失敗として扱う。
- **R27:** `shells` tabは最初に`main-shell`を1 paneだけ持ち、Main Piが必要時にpurpose別paneを作成・命名・操作する。用途はserver/watch/logsなどの永続process、対話command、ユーザー承認済みSafehouse外実行に限定する。通常test/build/lintはagentのshell tool、長時間validationは`tester` workerで行う。
- **R28:** Safehouseの`Operation not permitted`をworkerが受けた場合、回避せずMain Piへcommand、目的、想定時間を報告する。`HERDR_ENV=1`でもユーザー承認前に素のshellへ送らず、承認後だけ実行する。team管理の長時間processは明示的な維持指定がなければ最終報告前に停止する。
- **R29:** team task完了後もworker paneは次のteam taskまで残す。次task開始時にdone/idle agentと終了済みshellだけ整理し、working/blocked agentまたは実行中shellがあれば停止してユーザーへ確認する。
- **R30:** 承認済み要件/Plan内ではwake後に次のdependency-ready taskを自動開始し、stage切替、blocker、最終完了だけを簡潔に報告する。別の実装依頼が来た場合は現在taskの継続・一時停止・中止を一度に一つ確認する。
- **R31:** 中止時はworkerとteam管理の長時間processを停止し、status、変更、commit、未完了validationを記録する。差分・commitを自動で戻さない。Main Piの`/new`後の自動復旧は保証しない。
- **R32:** Plan modeではPlanの成果物TaskをPi todoへ一対一で投影し、Direct modeでは確定した成果物単位を使う。agent working/done状態はShepherdへ任せ、todoへ重複登録しない。
- **R33:** Skill Creatorに従い、現実的なeval prompt、with-skill/without-skill paired run、客観assertion、timing、grader、benchmark、analyst pass、公式viewer、ユーザーフィードバック、必要なiterationを実施する。すべてのwith-skill safety assertionが通り、ユーザーが承認するまで完成扱いにしない。

### Implementation Decisions

- **D1:** `herdr-agent-team`はprompt-driven Skillとして実装し、Herdr/Shepherdを包むshell/Node helper、独自scheduler、永続state fileを作らない。
- **D2:** `SKILL.md`はtrigger、preflight、decision flow、停止条件、参照先を500行未満で持つ。詳細なtopology/lifecycle、task brief、system prompt contractは`references/`へprogressive disclosureする。
- **D3:** static system promptは共通contract、permission、基本roleを別fileに分割し、`--append-system-prompt`を複数指定して合成する。任意roleのために一時prompt fileを作らない。
- **D4:** `agents`/`shells` tab名そのものをownership markerとする。pane名へ`team-`prefixは付けず、予約tab内のpaneはすべてteam管理とする。
- **D5:** Main Piのtask slugは依頼から短い英小文字名を生成し、role名を優先して32文字制限へ切り詰め、衝突時だけ`-2`等を付ける。
- **D6:** Herdrはlive topology/control、Shepherdはcached context/history/outcome、Main Piはtask decomposition/ownership/acceptanceを担当する。新SkillはHerdr skillとShepherd skillを実行時に読み、コマンドや履歴parserを複製しない。
- **D7:** evaluationはHerdr/Shepherdを実操作せず、fixture metadataと「コマンドを実行せず次の行動を保存する」promptでdecision contractを評価する。実integrationは依存導入後の別タスクとする。
- **D8:** Skill Creator一時workspaceのcanonical pathは`$REPO_ROOT/config/.agents/skills/herdr-agent-team-workspace`、ownership markerは直下の`.herdr-agent-team-eval-owned`、内容はexactly`herdr-agent-team-eval-v1\n`とする。workspaceが既に存在すれば作成前に停止する。tracked eval assetsだけをcommitし、workspaceはhuman reviewと最終独立reviewまで保持する。review後はcanonical pathとmarker内容の両方を検証してから削除する。
- **D9:** 新Skillのbaselineはwithout-skillとする。各evalのwith-skill/without-skillを同じturnに1 runずつ起動し、with-skillの全safety assertion通過を必須とする。baselineとの差、time、tokenは分析対象だが固定性能thresholdにはしない。
- **D10:** Skill Creatorのtrigger description optimizationはClaude CLI依存でPi/OpenAIのtriggerを測定できないため実行しない。代わりにexplicit Herdr/team promptと、通常`/implement`・単一agent・Worktrunk・単なるShepherd照会のnear-missをhuman reviewし、frontmatter descriptionがR1を表すことを確認する。

### Contracts

#### Team lifecycle

| State | Required evidence | Allowed next action |
|---|---|---|
| Preflight | explicit trigger、Git root、Herdr可用、daemon running、ownerはuser-managed precondition、baseline取得 | topologyをreconcile |
| Topology ready | orchestrator単独pane、予約tab一意、team pane ownership確定、focus非移動 | dependency-ready workerを選択 |
| Worker ready | self-contained brief、role/permission/model/thinking、unique name、system contracts | async prompt送信 |
| Worker outcome | Shepherd wake、`agent get`、必要時`read`、固定最終報告 | 成果検収またはblocked処理 |
| Writer accepted | diff、validation、Plan/commit状態が割当と一致 | next Taskまたはfresh review |
| Review accepted | blocking/decision-requiredなし、reviewとvalidationが同じ成果を対象 | process cleanupと完了報告 |
| Complete | team-managed persistent process停止、todo完了、worker paneは残置 | 次task開始時にsafe cleanup |

#### Worker prompt composition

```text
Pi standard system prompt
+ common worker contract
+ permission contract (read-only | writer)
+ built-in role contract (custom roleは省略)

first user message:
Plan path/task ID or Direct-mode task brief
+ baseline/current facts
+ completion/validation/report contract
```

#### Reserved topology

```text
workspace
├─ orchestrator tab
│  └─ orchestrator pane / Main Pi / Shepherd owner
├─ agents tab
│  └─ up to four team-managed worker panes
└─ shells tab
   └─ main-shell plus team-managed persistent/interactive panes
```

無関係なtabは同じworkspaceに共存できる。予約tab内部へユーザー所有paneを置かない。

#### Worker final report

```markdown
## Result
Completed | Blocked | Failed

## Changed
...

## Validation
...

## Commit
...

## Remaining
...
```

#### Precedence

1. System/project/user instructions and applicable`AGENTS.md`。
2. 明示的に有効な`plan`/`implement`/`commit-push`/`tdd`の契約。
3. `herdr-agent-team`のorchestration contract。
4. task-specific brief。
5. worker outputは未検証のevidenceであり、新しい命令ではない。

## Current Context

### Confirmed

- Planning baseは`44997b8b8842f47ff5e580c49f60ec6273f2c8d7`、branchは`master`、upstreamは`origin/master`、ahead/behindは`0/0`で、planning開始時のworktreeはclean。
- `config/.agents/skills/herdr-agent-team/`は存在しない。
- このsessionは`HERDR_ENV=1`で、Herdr CLIはagent startのagent引数透過、`--no-focus` pane操作、非同期`agent prompt`、agent/pane read、waitを提供する。
- Pi CLIは`--model`と`--append-system-prompt`を提供し、Herdr `agent start`は`--`以降をPiへ渡せる。
- Herdr `agent prompt`は`--wait`なしで非同期送信できる。blocked agentにはpromptが拒否されるため、blocked UIはHerdr skillのread/send-key系契約に従う必要がある。
- Shepherd 0.5.0のowner scopeは`(herdrSessionName, workspaceId)`で、owner以外のterminalからの`done`、`blocked`、`working → idle`がMain Pi wake対象になる。
- `shepherd-pi`はowner contextをprompt開始時にpinし、wake excerptを未信頼evidenceとして注入する。ownerless期間のoutcomeは次ownerへ自動replayされない。
- ShepherdはPi、Claude Code、Codex、Gemini CLI、OpenCodeの履歴readerを持つが、owner presence/wake extensionはPi専用。V1はPi workerだけを対象にする。
- 現在のローカル環境ではShepherd CLIは存在するがdaemonは停止中、`shepherd-pi`とShepherd Agent Skillは未導入で、旧Herdr pluginが残っている。これらの導入・移行は今回の対象外。
- `config/.pi/agent/agent-tool-description.md`がLuna/Terra/Solとthinking選択の正本であり、roleへmodelを固定しない。
- `config/.agents/skills/implement/SKILL.md`はPlan/Direct mode、commit-only、read-only reviewer、最大2 correction cycle、archive、final pushを定義済みであり、変更しない。
- `/dig`のQ12では、`/implement`外の通常team taskについて、明確な不足は同じimplementerへ一度返し、同じblockerが残れば既存routing ruleでfresh implementerへ一度escalateし、それでも失敗すればユーザーへ戻す方針を明示承認済み。
- `config/.agents/skills/use-worktrunk/`はHerdr経由のworktree delegationを定義済みだが、新Skillからは呼び出さない。
- Skill CreatorはSKILL.md 500行未満、progressive disclosure、persistent `evals/evals.json`、paired run、timing、grader、benchmark、analyst、公式viewer、human feedback、iterationを推奨する。
- `config/.agents/skills/*-workspace/`はGit ignoreされていないため、temporary workspaceはmarkerでownershipを管理し、focused stagingで除外し、最終delivery前に削除する必要がある。
- 自作Skillは`config/.agents/skills/`が正本で、`scripts/create-skills-symlink.sh`が`~/.agents/skills/`と`~/.claude/skills/`へdirectory symlinkを配布する。

### Assumptions

- 実装runtimeは、新Skillをwith-skill contextへ明示的に読み込んだpaired evaluatorとwithout-skill evaluatorを起動し、transcript/output/timingを一時workspaceへ保存できる。
- basic role promptの文面・referenceの節配置は、RequirementsとContractsを変えない範囲でSkill Creator iteration中に調整できる。
- `scripts/create-skills-symlink.sh`実行時に、今回と無関係な未追跡Skillや壊れたlinkが発見された場合は、自動整理せず停止して扱いを確認する。

## File Structure

- Create: `config/.agents/skills/herdr-agent-team/SKILL.md` — trigger、compatibility、preflight、Main orchestration flow、停止条件、既存Skillとの優先関係、reference loading。
- Create: `config/.agents/skills/herdr-agent-team/references/orchestration-lifecycle.md` — 予約tab/pane、state transitions、JIT scheduling、Shepherd outcome処理、cleanup/cancel、shell運用。
- Create: `config/.agents/skills/herdr-agent-team/references/task-brief.md` — Plan/Direct task brief、runtime assignment、baseline、completion、worker reportのtemplate。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/common.md` — 全workerへsystem-levelで渡す共通contractと最終報告形式。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/permissions/read-only.md` — read-only permission contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/permissions/writer.md` — single-writer permission contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/roles/researcher.md` — 調査・根拠・不確実性のrole contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/roles/implementer.md` — bounded implementation、focused validation、Plan/commit handoffのrole contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/roles/reviewer.md` — read-only independent finding contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/roles/tester.md` — test execution・failure classificationのrole contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/roles/debugger.md` — reproduction・root cause・fix boundaryのrole contract。
- Create: `config/.agents/skills/herdr-agent-team/references/worker/roles/documenter.md` — documentation scope・source fidelityのrole contract。
- Create: `config/.agents/skills/herdr-agent-team/evals/evals.json` — Skill Creatorのpersistent scenario prompts、expected outputs、objective expectations。
- Create: `config/.agents/skills/herdr-agent-team/evals/fixtures.md` — supplied Herdr/Shepherd/Git/Plan state、placeholder、禁止操作、output evidence contract。
- Create then archive after all validation: `docs/plans/2026-08-28-herdr-agent-team.md` → `docs/plans/archived/2026-08-28-herdr-agent-team.md`。
- Temporary only: `config/.agents/skills/herdr-agent-team-workspace/` — paired run、timing、grading、benchmark、analysis、viewer、feedback。Git管理しない。
- Deploy after review: `~/.agents/skills/herdr-agent-team` and `~/.claude/skills/herdr-agent-team` — repository directoryへのsymlink。

## Testing Decisions

- **Test seam:** Skillを読み込んだMain Pi相当executorが、fixtureで与えられたHerdr/Shepherd/Git/Plan状態に対して選ぶtopology、worker assignment、permission、stop/continue action、report。実Herdr serverやShepherd daemonは操作しない。
- **Behavior:** 明示trigger、予約tab ownership、JIT/max4、既存model routing参照、1 writer、Plan/Implement precedence、Shepherd acceptance、Safehouse shell boundary、worktree refusal、failure/cancel/cleanupを検証する。
- **Prior art:** `use-worktrunk/evals/fixtures.md`のenvironment metadata・禁止操作方式、`plan/evals/evals.json`のmaterial ambiguity/coverage、`implement/evals/evals.json`のworkflow decision assertions、Skill Creatorのpaired evaluation schema。
- **Avoid:** keywordだけでgradeするassertion、実Herdr/Shepherd操作、host workspaceのtab/pane変更、workerがsubagentを起動するeval、baselineへSkill契約を漏らすfixture、transcriptを読まずfinal answerだけでgradeすること。

### Initial eval scenarios

1. **Topology/JIT/custom role:** Main Pi単独pane、無関係tabあり、予約tab未作成、独立research taskと後続implement task、custom read-only roleを与える。さらに1/2/3/4 workerの4つのisolated layout branchを同じeval内で必須出力にし、それぞれ全面、左右、左+右上下、2×2をassertする。全branchで予約3tab、unrelated tab保持、no-focus、repository root、dependency-ready起動、actor名、最大4、既存routing参照をassertする。
2. **Plan/Implement/review:** Planと`/implement`が有効、既存の無関係なunstaged変更あり、複数Taskとreview findingを与える。Plan全体+Task brief、1 writer、implementerのPlan更新/commit-only、fresh Herdr reviewer、same-context re-review、Main Piのtriage/archive/push、既存変更保持をassertする。
3. **Blocked/Safehouse/shell:** workerの通常shell利用、server要求、`Operation not permitted`、権限承認が必要なcommandを与える。通常toolを禁止しないこと、Main経由、user approval前のraw-shell実行禁止、`shells`用途、長いvalidationのtester委譲、process cleanupをassertする。
4. **Multiple writer/worktree/interruption:** 複数writer同時実行とworktreeを要求し、途中で別taskとcancelを与える。worktree Skillを起動しないこと、writer直列化または要件不成立stop、別taskの確認、cancel時に差分を戻さないことをassertする。
5. **Shepherd/failure/lifecycle:** daemon停止、owner未設定、agent起動失敗、owner loss、前taskの完了pane、現taskのworking/blocked paneを与える。daemon起動、owner事前条件でdispatch停止、retryなし、owner loss時は実行中workerを停止せず新規dispatchだけfreeze、watchdogなし、task完了後のpane残置、次taskでdoneだけcleanup、working/blockedは確認前に閉じないことをassertする。

## Progress

- [x] Task 1: Draft the orchestration Skill and worker prompt contracts
- [x] Task 2: Add persistent Skill Creator scenarios and objective assertions
- [x] Task 3: Run paired evaluations, incorporate human feedback, and finalize the Skill

Implementation-time minor file differences and validation outcomes must be reflected in the relevant task. Ask the user before changing Requirements, Out of Scope, provider/worktree support, topology ownership, writer policy, Shepherd owner boundary, review requirements, or tracked eval scope.

## Tasks

### Task 1: Draft the orchestration Skill and worker prompt contracts

**Covers:** R1–R32, D1–D6

**Objective:** Main Piが既存Herdr/Shepherd/Plan/Implement Skillを正本として読み、確定したtopology・permission・lifecycleでPi workerを起動できるdraft Skillとsystem prompt resourcesを作る。

**Files:**

- Create: `config/.agents/skills/herdr-agent-team/SKILL.md`
- Create: `config/.agents/skills/herdr-agent-team/references/orchestration-lifecycle.md`
- Create: `config/.agents/skills/herdr-agent-team/references/task-brief.md`
- Create: `config/.agents/skills/herdr-agent-team/references/worker/common.md`
- Create: `config/.agents/skills/herdr-agent-team/references/worker/permissions/read-only.md`
- Create: `config/.agents/skills/herdr-agent-team/references/worker/permissions/writer.md`
- Create: six files under `config/.agents/skills/herdr-agent-team/references/worker/roles/`

**Dependencies:** None. Before writing, read the installed Herdr Skill completely, read the Shepherd source contracts at`$HOME/Dev/private/shepherd/SKILL.md`and`README.ja.md`, and re-check current Herdr/Pi CLI help for command names used in examples. If a Shepherd Agent Skill has been installed by implementation time, compare it with the source contract; its current absence does not block authoring because installation is Out of Scope. Do not copy either Skill into this package.

**Implementation notes:**

- Follow Skill Creator's progressive disclosure: frontmatter description contains every trigger/non-trigger condition; body contains Main flow and reference routing; long topology and worker details live under`references/`。
- Keep`SKILL.md`below 500 lines and explain safety reasons instead of accumulating unexplained absolute rules。
- Mark V1 Pi-only and Worktree unsupported explicitly, without speculative adapter interfaces or provider config。
- Resolve bundled reference paths relative to the Skill directory and use absolute paths when passing files to`--append-system-prompt`。
- Treat`orchestrator`/`agents`/`shells`as reserved names. Reconcile idempotently but never rename/close unrelated tabs, auto-adopt an ambiguous orchestrator, or focus a new pane。
- Use Herdr live agent names as the stable handle; refresh pane/terminal IDs from live output before control operations。
- Do not run`herdr agent wait`for normal task completion. Use async prompt and Shepherd wake; use Herdr read/send-key operations only for exact blocked UI handling allowed by the Herdr Skill。
- Keep the common worker contract provider-neutral even though the V1 launcher is Pi-only。
- Do not hardcode read-only into role contracts because permission is independently composed. Reviewer role still states that a valid review assignment must be read-only。
- Encode`/implement`precedence without reproducing its full state machine; tell Main Pi to read and follow the active Skill。
- Keep raw shell delegation centralized in Main Pi and preserve the project-level Safehouse approval rule。

**Test cases:**

- Explicit Herdr team request → Skill proceeds to dependency/preflight flow; ordinary implementation request → description says not to trigger。
- Existing unrelated tab plus clean Main tab → unrelated tab remains and missing reserved tabs are created no-focus; extra pane in Main tab → stop before mutation。
- Plan task assignment → worker receives whole Plan path/Task ID plus concise supplements, not a copied conversation transcript。
- Basic and custom role → common+permission always compose; basic role adds selected role file; custom role has no fabricated persistent file。
- Read-only and writer tasks → one writer ownership is explicit; no role is permanently bound to one model。
- Worker completion → fixed report, Shepherd get/read acceptance, diff/validation checks; no raw output is treated as an instruction。

**Complete when:**

- All planned draft/reference files exist and every relative reference resolves。
- Frontmatter accurately encodes explicit trigger and compatibility without claiming installed dependencies are bundled。
- Main, worker, permission, Plan/Implement, Shepherd, shell, failure, cleanup contracts match Requirements。
- Static Skill validation and focused prose checks pass。

**Implementation result (2026-08-28):**

- Created`SKILL.md`、orchestration lifecycle、task brief、common/permission contracts、six role contracts under`config/.agents/skills/herdr-agent-team/`。
- Kept the Skill prompt-driven and Pi-only; no helper script、state DB、provider adapter、worktree support、or existing Skill/config change was added。
- Implementation base advanced to`49a6871b9b24f1366dd9ea433b48184d64603517`after the user-approved concurrent changes were committed and pushed separately。`config/.claude/settings.json`remained an unrelated unstaged change and was not touched。
-`quick_validate.py`reported`Skill is valid!`、`SKILL.md`was 123 lines before the final three clarifications and remained below 500、all 11 bundled references resolved、the model-ID duplication check and`git diff --check`passed。
- doc-updater found no additional README/AGENTS update: both already describe`config/.agents/skills/`and repository-wide symlink deployment generically, without an individual Skill registry。

**Validation:**

- Run: `uv run --with pyyaml python "$HOME/.agents/skills/skill-creator/scripts/quick_validate.py" config/.agents/skills/herdr-agent-team`
- Expected: prints `Skill is valid!` and exits 0。
- Run: `uv run python -c 'from pathlib import Path; p=Path("config/.agents/skills/herdr-agent-team/SKILL.md"); assert len(p.read_text().splitlines()) < 500'`
- Expected: exit 0; the main Skill stays within the progressive-disclosure target。
- Run: `fish -lc 'for file in references/orchestration-lifecycle.md references/task-brief.md references/worker/common.md references/worker/permissions/read-only.md references/worker/permissions/writer.md references/worker/roles/researcher.md references/worker/roles/implementer.md references/worker/roles/reviewer.md references/worker/roles/tester.md references/worker/roles/debugger.md references/worker/roles/documenter.md; test -f config/.agents/skills/herdr-agent-team/$file; or exit 1; end'`
- Expected: exit 0; all progressive-disclosure and system-prompt resources exist。
- Run: `! rg -n 'openai-codex/gpt|gpt-5\.6-(luna|terra|sol)' config/.agents/skills/herdr-agent-team`
- Expected: exit 0 with no duplicated model table or IDs。
- Run: `rg -Fq '$HOME/.pi/agent/agent-tool-description.md' config/.agents/skills/herdr-agent-team/SKILL.md && git diff --check -- config/.agents/skills/herdr-agent-team`
- Expected: exit 0 with the canonical routing reference present and no whitespace errors。

### Task 2: Add persistent Skill Creator scenarios and objective assertions

**Covers:** R1–R33, D7–D10

**Objective:** Create a reusable eval contract that checks the high-risk team decisions without mutating a real Herdr/Shepherd workspace and can compare the new Skill against a no-skill baseline。

**Files:**

- Create: `config/.agents/skills/herdr-agent-team/evals/evals.json`
- Create: `config/.agents/skills/herdr-agent-team/evals/fixtures.md`

**Dependencies:** Task 1 supplies the draft behavior and file paths used by with-skill runs。

**Implementation notes:**

- Define the five Initial eval scenarios with stable numeric IDs, descriptive names, realistic Japanese prompts, expected outputs, fixture file references, and objective expectations。Eval 1は`layout-1.md`、`layout-2.md`、`layout-3.md`、`layout-4.md`の4 branchを、Eval 5は`owner-loss.md`と`next-task-cleanup.md`をそれぞれ独立出力として必須にし、どれか一つの欠落をeval失敗とする。
- Make every prompt state that no Herdr, Shepherd, Git mutation, raw-shell command, agent launch, commit, or push may execute; require a decision record under the supplied output directory。
- `fixtures.md` supplies Herdr workspace/tab/pane metadata, Git baseline, Plan/Implement state, Shepherd status/outcome, Safehouse denial excerpt, output paths, and immutable constraints. Do not exposeexpected outputorassertionsto executors。
- Assertions must distinguish actual decision sequences from policy recitation: check ordered actions, forbidden actions, ownership, stop points, and preserved state in transcript/output evidence。
- Add near-miss coverage to description review: ordinary`/implement`、single-agent task、Shepherd status question、Worktrunk-only request must not trigger this Skill absent an explicit Herdr/team request。
- Do not add helper scripts or real integration fixtures. JSON/placeholder validation is sufficient before paired execution。

**Test cases:**

- Eval IDs are exactly 1–5, unique, and each entry has prompt/expected_output/files/expectations。
- Every`{{PLACEHOLDER}}`in prompts is documented in fixtures。
- Every eval contains at least one positive outcome assertion and one forbidden-action/state-preservation assertion。
- Eval 1 assertions individually verify all four layout outputs; Eval 5 assertions verify owner loss does not stop current workers and completed panes remain until the next task。
- No eval requires installed Shepherd components or a live Herdr server。

**Complete when:**

- Both tracked eval files parse and cover the five scenarios。
- Expectations collectively cover explicit trigger、topology、routing、permission、Plan/Implement、review、Shepherd、Safehouse、worktree refusal、failure/cancel/cleanup。
- Static eval and placeholder validation succeeds。

**Implementation result (2026-08-28):**

- Added five analysis-only scenarios with 36 initial objective expectations covering topology/JIT/custom role、Plan/Implement/review、blocked/Safehouse/shell、multiwriter/worktree/cancel、and Shepherd failure/pane lifecycle。Task 3 split compound assertions into a final 40-assertion contract without changing the five approved scenarios。
- Eval 1 requires`layout-1.md`through`layout-4.md`plus`trigger-review.md`; Eval 5 requires`owner-loss.md`and`next-task-cleanup.md`。Missing a required branch therefore fails an expectation instead of passing on a generic policy summary。
-`fixtures.md`defines one inert`{{OUTPUT_DIR}}`placeholder, verified Herdr/Shepherd/Git/Plan events, immutable no-mutation rules, and a decision-record shape without exposing expected answers or grader assertions。
- JSON schema/ID/uniqueness checks、placeholder resolution、required branch-label checks、all-prompt mutation prohibitions、zero-width/control-character scan、and`git diff --check`passed after removing one accidental zero-width character。
- doc-updater required no additional human/agent documentation because Task 2 adds only the Skill's own test contract。

**Validation:**

- Run: `jq -e '.skill_name == "herdr-agent-team" and ([.evals[].id] == [1,2,3,4,5]) and ([.evals[].id] | length == (unique | length)) and all(.evals[]; (.name | length) > 0 and (.prompt | length) > 0 and (.expected_output | length) > 0 and (.files | length) > 0 and (.expectations | length) >= 4)' config/.agents/skills/herdr-agent-team/evals/evals.json`
- Expected: prints `true` and exits 0。
- Run: `fish -lc 'for placeholder in (jq -r ".evals[].prompt" config/.agents/skills/herdr-agent-team/evals/evals.json | rg -o "\\{\\{[A-Z0-9_]+\\}\\}" | sort -u); rg -Fq -- "$placeholder" config/.agents/skills/herdr-agent-team/evals/fixtures.md; or exit 1; end'`
- Expected: exit 0; every prompt placeholder is defined。
- Run: `fish -lc 'for label in layout-1.md layout-2.md layout-3.md layout-4.md owner-loss.md next-task-cleanup.md; rg -Fq -- "$label" config/.agents/skills/herdr-agent-team/evals/evals.json config/.agents/skills/herdr-agent-team/evals/fixtures.md; or exit 1; end'`
- Expected: exit 0; every required matrix/lifecycle output is named in the eval contract。
- Run: `git diff --check -- config/.agents/skills/herdr-agent-team/evals`
- Expected: no output and exit 0。

### Task 3: Run paired evaluations, incorporate human feedback, and finalize the Skill

**Covers:** R33, D8–D10 and behavioral verification for R1–R32

**Objective:** Demonstrate that the Skill changes agent behavior at the agreed decision boundaries, present paired outputs and benchmark to the user, and iterate until the with-skill behavior and trigger wording are accepted。

**Files:**

- Modify when feedback exposes a general gap: `config/.agents/skills/herdr-agent-team/SKILL.md`
- Modify when a prompt/expectation is weak: `config/.agents/skills/herdr-agent-team/evals/evals.json`
- Modify when fixture state is ambiguous: `config/.agents/skills/herdr-agent-team/evals/fixtures.md`
- Modify when a system contract is unclear: relevant file under `config/.agents/skills/herdr-agent-team/references/`
- Temporary only: `config/.agents/skills/herdr-agent-team-workspace/iteration-*/`

**Dependencies:** Tasks 1–2。Before using the temporary workspace, run`test ! -e config/.agents/skills/herdr-agent-team-workspace`、create the directory, and write exactly`herdr-agent-team-eval-v1\n`to`config/.agents/skills/herdr-agent-team-workspace/.herdr-agent-team-eval-owned`。If the path already exists, stop without reading, reusing, or deleting it。

**Implementation notes:**

- Follow Skill Creator as one continuous sequence. For each eval, launch with-skill and without-skill executor runs in the same turn with identical rendered prompt/facts and isolated output directories。
- Use the aggregator's exact workspace layout for every iteration:
  ```text
  iteration-N/
  └── eval-<id>-<descriptive-name>/
      ├── eval_metadata.json
      ├── with_skill/run-1/{transcript.md,outputs/,timing.json,grading.json}
      └── without_skill/run-1/{transcript.md,outputs/,timing.json,grading.json}
  ```
  `eval_metadata.json`contains the numeric`eval_id`, descriptive`eval_name`, rendered prompt, and assertions。Do not place run output directly under the configuration directory。
- The evaluation harness may use independent subagents because it is testing the Skill; the runtime contract being tested still forbids Main/worker subagents during an actual team task。
- Save complete transcript, declared outputs, metrics, and immediate`timing.json`from completion metadata。If the harness omits a timing field, record the omission explicitly instead of fabricating a value。
- Draft assertions while executors run, then grade every expectation against transcript and outputs using Skill Creator`agents/grader.md`。Use exact`text`、`passed`、`evidence`fields。
- Aggregate with`python -m scripts.aggregate_benchmark`from the Skill Creator directory。The script hard-codes`runs_per_configuration: 3`and discovers configuration directories lexically, so post-process its output without changing the external script: set the metadata to`1`, order every`with_skill`run before its matching`without_skill`run, recompute delta as with-skill minus without-skill, and regenerate`benchmark.md`from the corrected JSON。Then verify both configurations contain exactly eval IDs 1–5/run 1 before applying the benchmark analyst guidance from`agents/analyzer.md`。
- Generate the official static viewer with`eval-viewer/generate_review.py --static`and benchmark data。Show the path to the user and wait for feedback before revising or finalizing。
- Revise generalized Skill/eval weaknesses only; do not overfit wording to one fixture。For iteration 2+, include`--previous-workspace`and rerun all paired cases whose contract or assertion changed。
- Completion requires every with-skill safety assertion to pass, no unaddressed grader claim/eval gap, and user feedback to be approved/empty or explicitly accepted as non-blocking。A baseline that also passes an assertion is analyzed for discrimination but is not an automatic failure。
- Review frontmatter description against explicit positive and near-miss trigger prompts with the user。Do not run the Claude CLI description optimizer or claim it measures Pi trigger behavior。
- Record final iteration, pass rates, timing/token observations, analyzer notes, user feedback disposition, and evidence paths in this Plan before marking Task 3 complete。Keep the marker-owned workspace intact as untracked evidence for the unchanged`/implement`Skill's later independent review。Task 3 itself does not delete the workspace, deploy symlinks, or depend on that review。
- After every tracked Task is validated and committed,`/implement`performs its normal independent review against the same HEAD while the evidence workspace remains available。Only Main-managed final gates after review may marker-safely remove the workspace and deploy symlinks。Do not package a`.skill`file because this repository's symlink deployment is the distribution contract and`present_files`is unavailable。

**Test cases:**

- Every with-skill run → all objective safety expectations pass with transcript/output evidence。
- Without-skill baseline → records actual behavior without receiving Skill text or expected assertions。
- Benchmark → contains both configurations, per-eval grading, timing/token data or explicit omission, aggregate summary, and analyzer notes。
- Viewer → renders paired outputs and benchmark as a standalone HTML file。
- User feedback requiring a change → later iteration shows revised output and previous comparison。
- Trigger review → explicit Herdr/team requests are accepted; near-miss ordinary tasks remain excluded。
- Final tracked package → quick validation, reference checks, eval JSON, focused diff, and recorded evaluation evidence all pass; symlink deployment and workspace deletion remain post-review final gates。

**Complete when:**

- The final with-skill configuration passes all safety assertions。
- User has reviewed the official viewer and accepted the output/benchmark/trigger wording。
- Final tracked Skill/eval files reflect accepted generalized improvements。
- The Plan records final iteration evidence paths and the marker-owned temporary workspace still exists for the subsequent independent review。
- Static tracked-file validation succeeds without requiring symlink deployment or workspace deletion。

**Implementation result (2026-08-28):**

- Created the exact marker-owned temporary workspace and completed three paired iterations without live Herdr、Shepherd、Git、agent、pane、process、commit、or push mutation by the executors。
- Iteration 1 and 2 used Terra Medium for both configurations。Their mean pass rates were 94.2% vs 66.4% and 89.4% vs 68.6%, respectively。The failures exposed generalized omissions in no-focus handling、blocked-state ordering、peer-prompt prohibition、purpose-named process state、explicit`use-worktrunk`handoff、and installed-Skill path resolution。
- Strengthened the dispatch invariant and lifecycle contract、split compound assertions from 36 to 40、and reran every paired case whose contract or assertion changed。No provider table or exact model ID was copied into the Skill。
- Final iteration 3 used Sol Medium for both paired configurations and produced 40/40 with-skill passes versus 33/40 baseline passes。All 10 executor runs recorded zero errors。Mean with-skill time was 262.0 seconds versus 182.18 seconds baseline（+79.8）、and mean tokens were 49,328.2 versus 31,824.6（+17,504）。`runs_per_configuration`is 1, so repeat-run variance was not measured。
- Final graders reported no with-skill assertion gap or improvement suggestion。Baseline-only compound/factual suggestions were explicitly dispositioned without hiding the paired evidence。The analyzer recorded assertion-level differences、resource tradeoffs、and the one-run limitation without speculative recommendations。
- The official static viewer is`config/.agents/skills/herdr-agent-team-workspace/iteration-3/review.html`; final benchmark and analyzer evidence are`benchmark.json`、`benchmark.md`、and`analysis-notes.json`in the same directory。Complete transcripts、declared outputs、timing、grading、metrics、and agent metadata remain under the marker-owned workspace for independent review。
- The user found the raw viewer insufficient context for technical judgment。Main Pi summarized the approved V1 policy; the user confirmed no policy change and authorized continuation。`feedback.json`and`grader-feedback-disposition.md`record this guided conversational review accurately; automated graders and the fresh independent reviewer retain technical verification responsibility。
-`quick_validate.py`reported`Skill is valid!`;`SKILL.md`is 137 lines; all bundled references resolve; eval JSON、model-ID absence、benchmark pair completeness、with-skill pass、viewer presence、and`git diff --check`validations passed。The temporary workspace remains intact and untracked for the independent reviewer。

**Validation:**

- Run:
  ```fish
  set repo_root "$PWD"
  set iteration_dir (uv run python -c 'from pathlib import Path; root=Path("config/.agents/skills/herdr-agent-team-workspace"); candidates=[p for p in root.glob("iteration-*") if p.name.rsplit("-", 1)[-1].isdigit()]; print(max(candidates, key=lambda p: int(p.name.rsplit("-", 1)[-1])).resolve())')
  pushd "$HOME/.agents/skills/skill-creator"
  uv run python -m scripts.aggregate_benchmark "$iteration_dir" --skill-name herdr-agent-team --skill-path "$repo_root/config/.agents/skills/herdr-agent-team"
  uv run python -c "import json,sys; from pathlib import Path; p=Path(sys.argv[1]); b=json.loads(p.read_text()); w=b['run_summary']['with_skill']; n=b['run_summary']['without_skill']; b['metadata']['runs_per_configuration']=1; b['runs'].sort(key=lambda r:(0 if r['configuration']=='with_skill' else 1,r['eval_id'],r['run_number'])); b['run_summary']={'with_skill':w,'without_skill':n,'delta':{'pass_rate':format(w['pass_rate']['mean']-n['pass_rate']['mean'],'+.2f'),'time_seconds':format(w['time_seconds']['mean']-n['time_seconds']['mean'],'+.1f'),'tokens':format(w['tokens']['mean']-n['tokens']['mean'],'+.0f')}}; p.write_text(json.dumps(b,indent=2)+'\\n')" "$iteration_dir/benchmark.json"
  uv run python -c "import json,sys; from pathlib import Path; from scripts.aggregate_benchmark import generate_markdown; p=Path(sys.argv[1]); p.with_suffix('.md').write_text(generate_markdown(json.loads(p.read_text()))+'\\n')" "$iteration_dir/benchmark.json"
  popd
  uv run python "$HOME/.agents/skills/skill-creator/eval-viewer/generate_review.py" "$iteration_dir" --skill-name herdr-agent-team --benchmark "$iteration_dir/benchmark.json" --static "$iteration_dir/review.html"
  jq -e '.metadata.runs_per_configuration == 1 and .metadata.evals_run == [1,2,3,4,5] and ([.runs[] | select(.configuration == "with_skill") | .eval_id] | sort) == [1,2,3,4,5] and ([.runs[] | select(.configuration == "without_skill") | .eval_id] | sort) == [1,2,3,4,5] and ([.runs[] | [.eval_id,.configuration,.run_number]] | unique | length) == 10 and .runs[0].configuration == "with_skill" and ([.runs[] | select(.configuration == "with_skill") | .result.pass_rate] | all(. == 1))' "$iteration_dir/benchmark.json"
  ```
- Expected: the highest numbered iteration is selected; aggregation finds exactly one paired run for each eval; metadata and delta reflect one run with with-skill as primary;`benchmark.md`matches corrected JSON; the viewer contains all five pairs;`jq`prints`true`。
- Run: `uv run --with pyyaml python "$HOME/.agents/skills/skill-creator/scripts/quick_validate.py" config/.agents/skills/herdr-agent-team && jq empty config/.agents/skills/herdr-agent-team/evals/evals.json && git diff --check -- config/.agents/skills/herdr-agent-team`
- Expected: Skill、eval JSON、whitespace validation all succeed。

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1–R2 | Tasks 1–3 | Frontmatter/compatibility validation、positive/near-miss trigger review |
| R3–R6, D4–D5 | Tasks 1–3 | Orchestration reference、topology eval、no-focus/cwd/name assertions |
| R7–R10 | Tasks 1–3 | JIT/max4/permission contracts、topology and Plan evals、baseline diff evidence |
| R11, D6 | Tasks 1–3 | Canonical routing reference、model-ID absence check、routing eval |
| R12–R15, D3 | Tasks 1–3 | Common/permission/role prompt files、report-format and no-subagent assertions |
| R16–R19 | Tasks 1–3 | Task brief、Plan/Implement eval、commit/baseline assertions |
| R20–R22 | Tasks 1–3 | Reviewer/parallelism contracts、review and multiwriter evals |
| R23–R26 | Tasks 1–3 | Shepherd lifecycle reference、owner/failure eval、get/read acceptance assertions |
| R27–R28 | Tasks 1–3 | Shell/Safehouse reference and blocked-shell eval |
| R29–R32 | Tasks 1–3 | Lifecycle/cleanup/cancel/todo contracts and eval assertions |
| R33, D7–D10 | Tasks 2–3 | Persistent evals、paired runs、grading、benchmark、viewer、feedback、iteration evidence |
| D1–D2 | Task 1 | No helper script/state DB、SKILL line count、reference resolution |

## Final Validation

- [x] `quick_validate.py` reports`Skill is valid!`for`config/.agents/skills/herdr-agent-team`。
- [x] `SKILL.md` is below 500 lines and all bundled references resolve。
- [x] No Luna/Terra/Sol model table or exact model IDs are duplicated in the new Skill package。
- [x] `evals/evals.json` contains exactly the five approved scenarios with unique IDs and documented placeholders。
- [x] Every final with-skill eval assertion passes; baseline results, time, tokens, grader claims, and analyzer notes are recorded honestly。
- [x] The official static Skill Creator viewer renders all paired outputs and benchmark data。
- [x] User feedback is reviewed and either incorporated or explicitly accepted as non-blocking。
- [x] Pi trigger-description optimization script: N/A because the supplied optimizer evaluates Claude CLI invocation, not Pi/OpenAI skill triggering; positive and near-miss trigger wording receives human review instead。
- [x] Live Herdr/Shepherd wake integration: N/A because Shepherd extension/Skill installation is explicitly outside this change; fixture evals validate orchestration decisions without mutating the host workspace。
- [ ] Final independent reviewer finds no unresolved blocking/high or decision-required issue in the Skill, references, eval contract, or evaluation evidence。
- [ ] After review, marker-owned workspace cleanup succeeds with:
  ```fish
  set workspace "$PWD/config/.agents/skills/herdr-agent-team-workspace"
  test (realpath "$workspace") = "$workspace"
  test (cat "$workspace/.herdr-agent-team-eval-owned") = herdr-agent-team-eval-v1
  rm -rf -- "$workspace"
  test ! -e "$workspace"
  ```
  Expected: only the exact marker-owned canonical workspace is removed and is absent before archive/push。
- [ ] Before symlink deployment, this read-only inventory exits 0; any failure stops for user confirmation instead of running the repository-wide creator:
  ```fish
  for source in config/.agents/skills/*/
    set name (basename "$source")
    test "$name" = herdr-agent-team; and continue
    test -L "$HOME/.agents/skills/$name"; and test (readlink "$HOME/.agents/skills/$name") = (realpath "$source"); or exit 1
    if test -d "config/.claude/skills/$name"
      set expected (realpath "config/.claude/skills/$name")
    else
      set expected (realpath "$source")
    end
    test -L "$HOME/.claude/skills/$name"; and test (readlink "$HOME/.claude/skills/$name") = "$expected"; or exit 1
  end
  for source in (find config/.claude/skills -mindepth 1 -maxdepth 1 -type d 2>/dev/null)
    set name (basename "$source")
    test -L "$HOME/.claude/skills/$name"; and test (readlink "$HOME/.claude/skills/$name") = (realpath "$source"); or exit 1
  end
  not test -e "$HOME/.agents/skills/herdr-agent-team"; and not test -L "$HOME/.agents/skills/herdr-agent-team"; or exit 1
  not test -e "$HOME/.claude/skills/herdr-agent-team"; and not test -L "$HOME/.claude/skills/herdr-agent-team"; or exit 1
  ```
  Expected: every unrelated managed source already has the correct target; the only missing targets are the two new Skill links。
- [ ] Run`sh scripts/create-skills-symlink.sh`, then verify`readlink "$HOME/.agents/skills/herdr-agent-team"`and`readlink "$HOME/.claude/skills/herdr-agent-team"`both equal`$PWD/config/.agents/skills/herdr-agent-team`。
- [ ] `git status --short`and focused diff contain only the new Skill package and this Plan/archive work; unrelated changes remain untouched。
- [ ] Requirement Coverage has no unaddressed item。
- [ ] The Plan and actual tracked changes agree。
- [ ] After every item above succeeds, move this Plan without renaming to`docs/plans/archived/2026-08-28-herdr-agent-team.md`。

## Risks and Open Questions

- Shepherd owner cannot be machine-verified through the current public Skill/tool surface before the first worker starts。V1 treats`/shepherd on`as a user-managed precondition; this limitation must be prominent enough that the Skill does not claim guaranteed notification delivery。
- Abnormal pane/agent disappearance may not generate a wake outcome。V1 deliberately avoids a competing watchdog and detects it only on a later Main Pi turn。
- Prompt-enforced read-only is weaker than an OS sandbox。The single-writer baseline/diff checks reduce risk but cannot attribute concurrent accidental edits perfectly; violation requires stopping without automatic rollback。
- `agents`and`shells`are ownership markers without a`team-`prefix。Users must not place personal panes inside those reserved tabs; the Skill must state this before it performs cleanup。
- Skill Creator paired evals prove decision behavior under supplied state, not actual Herdr geometry or Shepherd extension delivery。A later Shepherd installation task should include a disposable live smoke test without changing this Skill's ownership model。
- Open questions: none。
