---
name: use-worktrunk
description: Worktrunkをこのdotfiles管理のAgent Safehouse環境で安全に操作するための環境アダプター。worktreeの作成、切替、ignoredファイルのコピー、削除、merge、pruneなど、エージェントが`wt`で実際にworktreeを操作するときは必ず使い、公式`worktrunk` Skillも読み込む。一般的なWorktrunkの仕様質問だけなら公式Skillを使う。
compatibility: Requires Worktrunk, the official worktrunk Skill, and this dotfiles repository's Agent Safehouse configuration.
---

# Worktrunk environment adapter

このSkillはWorktrunkの操作方法を置き換えない。公式`worktrunk` Skillへ、この環境のAgent Safehouse境界とAgent sessionの制約だけを補う。

## 1. 公式Skillと現在のCLIを先に確認する

`wt`で実際に操作する前に、必ず次を読む。

```text
~/.agents/skills/worktrunk/SKILL.md
```

存在しなければ操作を停止し、次を案内する。公式Skillの内容を推測して続けない。

```bash
cd ~ && npx skills experimental_install
```

関連する`wt <command> --help`も現在のCLIから確認する。作成、hook、approval、copy、merge、remove、pruneなどの意味と既定値は公式SkillとCLIに従い、このSkillで再定義しない。一般的なWorktrunkの仕様質問だけなら公式Skillへ委譲し、この環境制約を持ち込まない。

`--yes`でproject commandのapprovalを迂回しない。forceや破壊的なoptionは、ユーザーが明示して承認した場合以外は追加しない。

## 2. 操作前にSafehouse境界を分類する

予定path、tracked file、ignored-file copy、またはsandbox拒否が関係するときだけ、現在の正本を読む。

```text
~/dotfiles/config/.config/fish/functions/__safehouse_args.fish
~/dotfiles/config/.config/agent-safehouse/local-overrides.sb
```

`wt config show --format=json`と、必要なら`wt hook show --expanded`で有効な設定とdirect hookも確認する。allowlist、deny pattern、hookをSkill本文から推測しない。

新規作成をAgent内で行う前に、予定destinationとtarget commitのGit tree path名を安全なGit metadataから確認する。実ファイルをprobeせず、`local-overrides.sb`のrule順序と後勝ちallowを含めて最終的なaccessを判断する。tracked pathが最終denyになる場合、または確信を持って判断できない場合は作成を通常shellへ委譲する。このpreflightは既存worktreeの選択には行わない。

`.worktreeinclude`が存在するだけではcopyが実行されるとは判断しない。ユーザーがcopyを明示した場合、または有効な作成hookが`wt step copy-ignored`を直接呼ぶ場合だけcopy workflowとして扱う。任意のshell script内部までは解析しない。

## 3. Agent内で実行する操作と通常shellへ委譲する操作

| 操作 | Agent Safehouse内の扱い |
|---|---|
| 既存worktreeの選択 | `--no-cd --format=json`で実行可能 |
| grant内への新規作成。tracked denyもdirect copy hookもない | tracked path preflight後に`--no-cd --format=json`で実行可能 |
| 明示的な`wt step copy-ignored` | dry-runを含めて実行しない。通常shellへ委譲 |
| direct copy hookを伴う新規作成 | 作成から通常shellへ委譲 |
| 現在のsessionのgrant外への新規作成 | 設定を変えず、作成から通常shellへ委譲 |
| tracked pathが最終deny、またはpolicy評価が不確実な新規作成 | 作成から通常shellへ委譲 |
| `wt step promote`、`wt remove`、live `wt step prune` | 通常shellへ委譲 |
| cleanupを伴う`wt merge` | 通常shellへ委譲 |
| ユーザーが明示した`wt merge --no-remove` | Agent内で実行可能 |
| `wt step prune --dry-run` | Agent内で実行・要約可能。live実行は確認後に通常shellへ委譲 |

`copy-ignored`は対象の実在や安全なfileだけを選別しない。Agent内でdry-runや部分copyを行わず、元の`--from`、`--to`、`--require-include`、include/exclude条件を保持したreal commandを通常shell向けに案内する。copy用dry-runは追加しない。

委譲commandへ`--foreground`、`--force`、`--force-delete`、`--yes`、`--no-remove`などを都合よく追加しない。ユーザーが指定したflagとWorktrunkの既定動作を保つ。

## 4. Agent sessionから通常switchする

現在のAgent sessionが通常の`wt switch`で別worktreeを選択・作成しても、shell integrationは親Agentのcwdやinstruction discoveryを確実には変更できない。ユーザーの引数を保ち、次を追加する。

```text
--no-cd --format=json
```

raw JSONを確認し、返されたworktree pathが絶対pathであることを検証する。選択・作成後はそのworktreeで実装や編集を始めず、pathと新しいAgent sessionが必要なことを報告して停止する。

既存worktreeを選択しただけなら、creator/coordinatorや新規作成用fork workflowとして説明しない。検証済みpathから新しいsessionを開始するよう案内する。

新規作成に成功した場合は、現在のsessionをcoordinatorとして元のworktreeに残し、会話を独立workerへforkするcommandを報告する。forkは自動実行しない。

```text
Pi:          cd <worktree-path> && pi --fork <session-id>
Claude Code: cd <worktree-path> && claude --resume <session-id> --fork-session
Codex:       codex fork -C <worktree-path> <session-id>
OpenCode:    opencode <worktree-path> --session <session-id> --fork
```

clientとsession IDは、ユーザーが明示した値、system context、または信頼できるruntime metadataから特定する。clientが不明なら推測せず4 commandをlabel付きで示す。session IDを取得できなければ`<session-id>`を残して置換が必要だと説明し、session store、transcript、credential、Safehouse deny対象を探らない。pathと引数はshell-safeにquoteする。

Claude Codeのin-session `/fork`や`--worktree`は使わない。Codexの`resume -C`、OpenCodeのplain `--session` resumeやsession moveではなく、独立forkを使う。

ユーザーが一般commandの`--execute`、terminal multiplexer、またはsub-agent handoffを明示し、他に通常shellへの委譲条件がなければ、通常switch規則へ置き換えず公式Skillのhandoff workflowへ委譲する。

## 5. 通常fish shellへ委譲する

Agent内では、通常shell向けcommandを報告するだけで実行しない。新規作成とblocking copyが一つの依頼なら、途中のworktreeをAgentが先に作らず、作成、copy、Agent起動を最初から順に案内する。後続のblocking stepは前段成功時だけ進む形にする。

`pre-start` copyはblockingなので、switch成功後にAgentを起動できる。`post-start` copyはbackground/non-blockingという設定意図を尊重し、完了をAgent起動条件にしない。ユーザーがpost-start完了を明示的に必要とする場合は`pre-start`への移動を提案するが、project configとuser configのどちらも明示的な同意前には編集しない。

委譲workflowでAgent CLIがWorktrunk `--execute`に指定されていても、Worktrunk child shellはfishのSafehouse wrapperを読み込むとは限らない。Agent CLIの`--execute`をWorktrunk commandから外し、blocking step成功後に対話中のfishから`pi`、`claude`、`codex`、`opencode` wrapperを別commandで起動する。元の`--`以降にAgentへ渡す引数があれば、Worktrunk commandへ残さず、現在のclient helpに従ってshell-safeにAgent wrapper側へ移す。一般の非Agent `--execute`にはこの例外を広げない。自動multiplexer handoffは組み立てない。

blocking commandが作成後に失敗した場合はworkflowを停止してworktreeを残し、copyの自動retry、remove、rollback、Agent起動を行わない。診断が必要なら、提示済みのexit statusを使い、未提示ならそれを確認したうえで、秘密値を伏せたエラー周辺だけを依頼する。full hook logや環境変数値を貼るよう求めない。

## 6. 削除・交換後のsessionを扱う

委譲した`promote`、remove、merge cleanup、live pruneが現在のAgent worktreeを削除または入れ替える場合、command実行後は現在のsessionを継続しない。必要な作業は新しいAgent sessionから始める。対象が無関係なsibling worktreeだけなら現在のsessionは継続できる。

live pruneはAgent内のdry-run結果を候補として要約し、ユーザー確認を得てから通常shell commandを案内する。dry-run時の選択条件を保ち、確認前にlive実行済みとして扱わない。

## 7. sandbox拒否と結果を報告する

`Operation not permitted`や`deny(`に遭遇したら再試行で押し切らない。次のSkillを読み、失敗command、errorに現れたpath、現在のpolicyから診断する。

```text
~/.agents/skills/use-agent-safehouse/SKILL.md
```

force、policy緩和、deny対象へのprobeで回避しない。Safehouse設定またはWorktrunk設定そのものの変更をユーザーが求める場合は、理由と最小変更を提示し、同意後にだけ編集する。

結果では、実行したWorktrunk commandの結果、検証済み絶対path、Agent内では実行せず通常shellへ委譲したcommand、現在のsessionを継続できるか、新しいAgent sessionが必要かを簡潔に返す。project hookがない場合にsetupやbaseline testを推定しない。
