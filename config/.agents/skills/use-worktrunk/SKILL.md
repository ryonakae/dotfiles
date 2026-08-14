---
name: use-worktrunk
description: Worktrunkをこのdotfiles管理のAgent Safehouse環境で安全に操作するための環境アダプター。worktreeの作成、切替、ignoredファイルのコピー、削除、merge、pruneなど、エージェントが`wt`で実際にworktreeを操作するときは必ず使い、公式`worktrunk` Skillも読み込む。一般的なWorktrunkの仕様質問だけなら公式Skillを使う。
compatibility: Requires Worktrunk, the official worktrunk Skill, and this dotfiles repository's Agent Safehouse configuration.
---

# Worktrunk environment adapter

このSkillはWorktrunkの操作方法を置き換えない。公式`worktrunk` Skillに、この環境のAgent Safehouse境界とAgentセッションの制約だけを補う。

## 1. 公式Skillを先に読む

`wt`で実際に操作する前に、必ず次を読む。

```text
~/.agents/skills/worktrunk/SKILL.md
```

存在しなければ操作を停止し、次の復元コマンドを案内する。公式Skillの内容を推測して続けない。

```bash
cd ~ && npx skills experimental_install
```

一般的なWorktrunkの仕様質問だけなら公式Skillへ委譲し、このSkillの環境制約を持ち込まない。

## 2. Worktrunkの既定動作を保つ

作成、hook、approval、copy、merge、remove、pruneなどの意味と既定値は、公式Skillと現在の`wt <command> --help`に従う。ユーザーが明示した場合、または以下の環境制約に必要な場合だけフラグを追加・変更する。

`--yes`でproject commandのapprovalを迂回しない。forceや破壊的なoptionは、ユーザーが明示して承認した場合以外は使わない。

## 3. 関係するときだけSafehouse境界を確認する

worktreeの予定path、relocate、ignored-file copy、またはsandbox拒否が関係するときだけ、現在の正本を読む。

```text
~/dotfiles/config/.config/fish/functions/__safehouse_args.fish
~/dotfiles/config/.config/agent-safehouse/local-overrides.sb
```

allowlistやdeny patternをこのSkillの記憶や本文から推測しない。`wt config show --format=json`で現在のWorktrunk設定も確認する。

予定pathが書き込み許可範囲外なら、失敗すると分かった操作を実行しない。Safehouseを広げるより、既存grant内を使うWorktrunk user config変更を提案する。user configは個人設定なので、公式Skillに従って編集前にユーザーの同意を得る。

## 4. Agentセッションからswitchする

現在のAgentセッションを通常の`wt switch`で別worktreeへ移す場合、shell integrationは親Agentのcwdやinstruction discoveryを確実には変更できない。ユーザーの引数とWorktrunk既定動作を保ちつつ、次を追加する。

```text
--no-cd --format=json
```

raw JSONを確認し、返されたworktree pathが絶対pathであることを検証する。作成または選択後は、そのworktreeで実装や編集を始めない。結果と絶対pathを報告し、そのpathから新しいAgentセッションを開始するよう案内して停止する。

ユーザーが`--execute`、terminal multiplexer、またはsub-agentへのhandoffを明示した場合はこの通常switch規則を適用せず、公式Skillのhandoff workflowへ委譲する。公式workflowが別プロセスを対象worktreeで開始するため、親Agentのcwd問題とは分けて扱う。

通常switchで新しいworktreeを作成した場合、現在のセッションは並行開発のcoordinatorとして元のworktreeに残し、会話を独立workerへforkする次の手順を案内する。fork commandは自動実行しない。

現在のclientとsession IDは、ユーザーが明示した値、system context、または信頼できるruntime metadataから特定し、検証済み絶対pathとともにshell-safeにquoteして対応する形を報告する。

```text
Pi:          cd <worktree-path> && pi --fork <session-id>
Claude Code: cd <worktree-path> && claude --resume <session-id> --fork-session
Codex:       codex fork -C <worktree-path> <session-id>
OpenCode:    opencode <worktree-path> --session <session-id> --fork
```

Claude Codeのin-session `/fork`や`--worktree`はClaude独自のworktreeを作り得るため使わない。並行workerには、Codexの`resume -C`、OpenCodeのplain `--session` resumeやsession moveではなく、表の独立forkを使う。

clientを確実に特定できなければ推測せず、4 commandをclient label付きで全て示す。session IDはユーザーが明示した場合、または信頼できるruntime metadataにある場合だけ具体値を使う。取得できなければ`<session-id>`を残して置換が必要だと説明し、session store、transcript、credential、Safehouseのdeny対象を探らない。

## 5. ignored fileをコピーする

Agent Safehouse内では、policyがdenyするpathを直接probe、read、copy、create、edit、removeしない。読んでよいのはSafehouse policy、`.worktreeinclude`、WorktrunkのJSON planなど、deny対象ではない設定・metadataだけである。

1. `local-overrides.sb`と`.worktreeinclude`から、選択対象のうちdenyされる名前を特定する。
2. `wt config show --format=json`でsystem config、project config、user global、matching project overrideの`step.copy-ignored.exclude`を確認する。表示はresolved配列ではないため、存在する全sourceのpatternを漏れなく集める。有効な既存patternにunescaped negation（先頭が`!`）があれば、dry-run後の未知entryを再許可し得るためAgent内real copyは行わず、通常shellへ委譲する。negationがなければ、既存excludeを保持し、deny対象を加えたinvocation-scopedな`step.copy-ignored.exclude`を組み立て、元の引数を保ったまま`--dry-run --format=json`を実行する。
3. initial planで観測した`kind: dir` pathを記録し、既存exclude適用済みのplanに現れた`kind: file`のうちpolicyが許すpathだけをapproved filesとする。planに現れなかったpathやdirectoryをapprovedへ足さない。Worktrunkはreal copy時にsourceを再走査するため、観測済みdirectoryの個別除外だけではdry-run後に増えたentryを防げない。
4. final invocationのexcludeを、gitignore pattern `*`、approved fileごとのexact negation pattern（例: `!build-cache.bin`）、directory pattern `*/`、手順2で集めた全sourceの既存exclude、deny対象の順に含む値へ置き換える。approved file以外のnegationは生成しない。`*/`をnegationより後に置き、approved fileがdry-run後に同名directoryへ置換されても再帰copyしない。`--config-set`がuser global配列を置換し、前段でmergeされたproject excludeより後に評価される場合もあるため、既存patternを末尾側へ再配置する。後勝ちの既存excludeとdenyをapproved filesより優先し、元設定で除外済みのfileを再許可しない。file path内のgitignore metacharacterはliteralとしてescapeする。同じ入力で2回目の`--dry-run --format=json`を実行し、entriesがapproved filesと完全一致し、全て`kind: file`であることを確認する。
5. 2回目と同一のexclude・from・to・include条件で、`--dry-run`だけを外して実行する。`*`によるdeny-by-defaultを保つため、dry-run後に増えたroot fileやdirectoryはreal copyの再走査でも対象にならない。

どちらかのdry-runが`Operation not permitted`になった場合、approved filesだけのexact planにできない場合、path patternを安全にescapeできない場合、または有効な既存excludeを保持できない場合は、real copyを行わない。force、policy緩和、対象pathへのprobeで回避しない。

Agent側で除外したdeny対象とinitial planで観測したrecursive directoryは、その名前だけを報告する。ユーザーがコピーを必要としている場合は、内容を読まず、Safehouse外の通常shellで実行するWorktrunkのdry-runと本実行手順を案内する。このfile-only制約はAgent Safehouse内だけの補完であり、通常shellでのWorktrunk既定動作は変更しない。

## 6. sandbox拒否を扱う

`Operation not permitted`や`deny(`に遭遇したら再試行で押し切らない。次の`use-agent-safehouse` Skillを読み、失敗したcommandとerrorに現れたpath、現在のpolicyを使って診断する。

```text
~/.agents/skills/use-agent-safehouse/SKILL.md
```

Safehouse設定またはWorktrunk user configの変更が必要なら、理由と最小変更を提示し、ユーザーの同意後にだけ編集する。

## 7. 結果を報告する

簡潔に次を返す。

- Worktrunk commandの結果
- worktreeを作成・選択した場合は検証済みの絶対path
- 通常switchで新規作成した場合は、creatorを残す理由とclient別の独立fork command（選択のみ、または明示的handoffなら不要）
- Agent側で扱わなかったdeny対象またはrecursive entryと、必要な通常shell操作
- 新しいAgentセッションが必要か

project hookがない場合にsetupやbaseline testを推定しない。ユーザーが別途依頼したsetup/testは通常の開発作業として扱う。
