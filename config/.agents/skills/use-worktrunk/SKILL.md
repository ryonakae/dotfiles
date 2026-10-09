---
name: use-worktrunk
description: Worktrunkをこのdotfiles管理のAgent Safehouse環境で安全に操作するための環境アダプター。worktreeの作成、切替、ignoredファイルのコピー、削除、merge、pruneなど、エージェントが`wt`で実際にworktreeを操作するときは必ず使い、公式`worktrunk` Skillも読み込む。Safehouse内外の判定を行い、現在のgrant外に及ぶ操作を事前に委譲する。herdr環境（HERDR_ENV=1）では委譲操作をherdrペインで実行し、作成したworktreeをherdrのworkspaceとしてsidebarへ登録し、fork依頼はそのworkspaceでのfork起動まで完遂する。herdrがなければ通常shellへ案内する。一般的なWorktrunkの仕様質問だけなら公式Skillを使う。
compatibility: Requires Worktrunk, the official worktrunk Skill, and this dotfiles repository's Agent Safehouse configuration.
---

# Worktrunk environment adapter

このSkillはWorktrunkの操作方法を置き換えない。公式`worktrunk` Skillへ、この環境のAgent Safehouse境界とAgent sessionの制約だけを補う。Safehouse外で動いているsessionにはSafehouse境界の制約を持ち込まない。

## 0. 依頼が操作か質問かを最初に分ける

このSkillの規則は、`wt`で実際にworktreeを操作する依頼にだけ効く。Worktrunkの仕様、設定値の意味、hookの選び方を尋ねられただけなら、§1で公式Skillを読み、その知識だけで答えて終える。§2以降の環境判定・境界分類・委譲へは進まず、Safehouse、通常shellへの委譲、Agent起動、fork、session継続を答えに持ち込まない。

仕様質問にこの環境の事情を混ぜると、読み手はWorktrunk自体がそう振る舞うと誤解する。ユーザーの環境が変わればこのSkillの結論は変わるが、Worktrunkの仕様は変わらない。分けて答える価値はそこにある。

迷ったら、その依頼を果たすときに実際に`wt`が実行されるかで決める。実行されないなら質問として扱う。

## 1. 公式Skillと現在のCLIを先に確認する

`wt`で実際に操作する前に、必ず次を読む。

```text
~/.agents/skills/worktrunk/SKILL.md
```

存在しなければ操作を停止し、`~/dotfiles/.agents/skills/dotfiles-setup/references/setup.md`「外部スキル」に従って、固定済みの Nix 構成を build / switch して復元するよう案内する。最新版の再取得や公式Skillの内容を推測して続けることはしない。

Agent内で実行するcommand、およびflagの意味に新たに依存して委譲commandを組み立てる場合は、実行前に`wt <command> --help`を現在のCLIから確認する。古い知識でflagを組み立てる事故を防ぐためで、ユーザー指定のflagを原文のまま保持して委譲するだけなら不要。作成、hook、approval、copy、merge、remove、pruneなどの意味と既定値は公式SkillとCLIに従い、このSkillで再定義しない。一般的なWorktrunkの仕様質問だけなら公式Skillへ委譲し、この環境制約を持ち込まない。

`--yes`でproject commandのapprovalを迂回しない。機密情報へのアクセス・コピーと破壊的操作は、実行先に関わらず事前承認を得る。forceや破壊的なoptionは、ユーザーが明示して承認した場合以外は追加しない。

## 2. 実行環境を判定する

§0で操作と判断した依頼にだけ、最初の`wt`操作の前に、現在のsessionがAgent Safehouse内かを環境変数で判定する。

```sh
test "$APP_SANDBOX_CONTAINER_ID" = agent-safehouse
```

- 一致すればSafehouse内。§3の境界分類と§4の委譲表に従い、現在のgrant外に及ぶ操作を事前に委譲する。委譲先は下記のherdr判定で決まる。
- 未設定または別値ならSafehouseの制限はない。§3と§4は適用せず、ignored-file copy、cleanupを伴う`wt merge`、`wt remove`、live pruneも含めてAgent内で実行し、通常shellでの実行をユーザーに求めない。
- どちらの環境でも変わらない規則: §1の承認ルール（`--yes`迂回禁止、force系optionの勝手な追加禁止）、§5のsession制約（switchしても親Agentのcwdは変わらない）、§7のsession継続判断（自worktreeの削除・入替後はsessionを継続しない）。

Safehouse判定と独立に、herdrが使えるかも判定する。

```sh
test "$HERDR_ENV" = 1
```

一致し、かつ最初のherdr CLI呼び出し（例: `herdr pane current --current`）が成功すればherdr有効。herdr CLIが利用できなければ無効として扱う。実行拒否の場合は§8に従い停止する。組み合わせで変わるのは委譲先とforkの完遂可否だけで、§3の境界分類、§4の操作分類、§1の承認ルールは変わらない。

- Safehouse内 × herdr有効: §3・§4が委譲とした操作を`references/herdr-delegation.md`の手順でherdrペインで実行する。委譲対象のうち破壊的操作（`wt remove`、cleanupを伴う`wt merge`、live `wt step prune`、`wt step promote`）は実行前にユーザー承認を得る。それ以外の委譲操作（作成・switch、copy-ignored）は非秘密の操作なら承認なしで実行してよい。機密情報へのアクセス・コピーは実行先に関わらず事前承認を得る。§4がAgent内で実行可能とする操作（`wt merge --no-remove`、`wt step prune --dry-run`など）は従来どおりAgent内で実行し、herdrへ回さない
- Safehouse内 × herdr無効: 委譲操作は§6の通常shell案内に従う
- Safehouse外 × herdr有効: `wt`はAgent内で実行し、herdrは§5のfork完遂にだけ使う
- Safehouse外 × herdr無効: すべてAgent内で実行し、forkは§5の報告に留める

判定はsessionにつき一度でよく、以降の`wt`操作では結果を再利用する。判定に関わらず、実行拒否（`Operation not permitted`、`deny(`）に遭遇したら§8に従い報告して停止する。

## 3. Safehouse内では操作前に境界を分類する

この節は§2でSafehouse内と判定した場合だけ適用する。予定path、copy、削除・交換が関係するときに、現在の正本を確認する。

```text
~/dotfiles/config/.config/fish/functions/__safehouse_args.fish
~/dotfiles/config/.config/agent-safehouse/compatibility.sb
~/dotfiles/config/.config/agent-safehouse/local-overrides.sb
```

`wt config show --format=json`と、必要なら`wt hook show --expanded`で予定destinationと有効なdirect hookを確認する。現在のwrapperはHOME RWを許可する。HOME外ではworkdir・`--add-dirs`の書き込みgrantを確認し、読み取り用の`wide-read`と区別する。起動時のpolicyが判定対象で、正本を編集しても現在のsandboxは更新されない。

事前委譲は予定操作が現在のgrant外に及ぶと確認できた場合に限る。必要なpathが不明なら、その情報を確認して実行先を決める。拒否を試す目的でコマンドを実行しない。

`.worktreeinclude`が存在するだけではcopyが実行されるとは判断しない。ユーザーがcopyを明示した場合、または有効な作成hookが`wt step copy-ignored`を直接呼ぶ場合だけcopy workflowとして扱う。任意のshell script内部までは解析しない。

### copyをAgent内で実行できるか評価する

copy workflowでは解決後の`--from`/`--to`のabsolute pathと必要な読み書き権限を確認する。必要なgrant内であれば、`wt step copy-ignored`（direct hook経由を含む）をAgent内で実行できる。機密情報へのアクセス・コピーには事前承認を得る。

grant外のため事前委譲する場合は、copy全体と元のinclude/exclude条件を保持する。

### 削除・交換の境界を評価する

`promote`、remove、merge cleanup、live pruneは、対象pathが現在のgrant外に及ぶと確認できた場合に事前委譲する。それ以外はAgent内で実行できる。破壊的操作の事前承認と§7のsession制約はどちらの実行先でも維持する。

## 4. Agent内で実行する操作と委譲する操作

この表は§2でSafehouse内と判定した場合だけ適用する。Safehouse外では委譲せずAgent内で実行する。表の「通常shellへ委譲」は「Agent内では実行しない」という操作分類であり、実際の委譲先は§2のherdr判定に従う。herdr有効なら`references/herdr-delegation.md`の手順でherdrペインで実行し（§2の破壊的操作はユーザー承認後）、無効なら§6の案内に落とす。

| 操作 | Agent Safehouse内の扱い |
|---|---|
| 既存worktreeの選択 | `--no-cd --format=json`で実行可能 |
| grant内への新規作成 | `--no-cd --format=json`で実行可能 |
| 明示的な`wt step copy-ignored` | §3で必要な権限と承認を確認して実行先を決める |
| direct copy hookを伴う新規作成 | §3のcopy評価に従う。委譲が必要なら作成から通常shellへ委譲 |
| 現在のsessionのgrant外への新規作成 | 設定を変えず、作成から通常shellへ委譲 |
| `wt step promote`、`wt remove`、live `wt step prune` | §3の削除・交換評価に従う。事前承認後に実行 |
| cleanupを伴う`wt merge` | 同じ削除・交換評価に従う |
| ユーザーが明示した`wt merge --no-remove` | Agent内で実行可能 |
| `wt step prune --dry-run` | Agent内で実行・要約可能。live実行は確認後に§3の削除・交換評価で実行先を決める |

copyを委譲する場合、`copy-ignored`の対象を実在や安全なfileだけに選別しない。Agent内でdry-runや部分copyを行わず、元の`--from`、`--to`、`--require-include`、include/exclude条件を保持したreal commandを、§2の判定に従いherdrペインで実行するか通常shell向けに案内する。copy用dry-runは追加しない。

委譲commandへ`--foreground`、`--force`、`--force-delete`、`--yes`、`--no-remove`などを都合よく追加しない。ユーザーが指定したflagとWorktrunkの既定動作を保つ。

## 5. Agent sessionから通常switchする

この節はSafehouse内外に関わらず適用する。現在のAgent sessionが通常の`wt switch`で別worktreeを選択・作成しても、shell integrationは親Agentのcwdやinstruction discoveryを確実には変更できない。ユーザーの引数を保ち、次を追加する。

```text
--no-cd --format=json
```

raw JSONを確認し、返されたworktree pathが絶対pathであることを検証する。選択・作成後はそのworktreeで実装や編集を始めず、pathと新しいAgent sessionが必要なことを報告して停止する。

既存worktreeを選択しただけなら、creator/coordinatorや新規作成用fork workflowとして説明しない。検証済みpathから新しいsessionを開始するよう案内する。

新規作成に成功した場合は、現在のsessionをcoordinatorとして元のworktreeに残し、会話を独立workerへforkするcommandを報告する。後述のherdr fork flowの条件を満たす場合を除き、forkは自動実行しない。

```text
Pi:          cd <worktree-path> && pi --fork <session-id>
Claude Code: cd <worktree-path> && claude --resume <session-id> --fork-session
Codex:       codex fork -C <worktree-path> <session-id>
OpenCode:    opencode <worktree-path> --session <session-id> --fork
```

clientとsession IDは、ユーザーが明示した値、system context、または信頼できるruntime metadataから特定する。clientが不明なら推測せず4 commandをlabel付きで示す。session IDを取得できなければ`<session-id>`を残して置換が必要だと説明し、session store、transcript、credentialを探らない。pathと引数はshell-safeにquoteする。

Claude Codeのin-session `/fork`や`--worktree`は使わない。Codexの`resume -C`、OpenCodeのplain `--session` resumeやsession moveではなく、独立forkを使う。

### herdr fork flow

次のすべてを満たす場合は、コマンド報告の代わりに`references/herdr-delegation.md`のfork手順で、一時ペインでの`wt switch`、`herdr worktree open`によるworkspace登録、そのworkspaceでの`herdr agent start`によるfork起動、引き継ぎpromptの送信まで自動実行する。Safehouse内外は問わない。

- §2でherdr有効と判定した
- ユーザーがfork・引き継ぎの意図を示した（例:「worktreeを作ってそっちで作業して」）。worktreeの作成だけの依頼では発動しない
- clientとsession IDを上記の規則で特定できた

このflowでは`wt switch`をAgentのsessionではなくherdrペインの対話shellで実行するため、この節の`--no-cd --format=json`規則は適用せず、reference手順に従う。起動と送信の完了を報告した後、現在のsessionはcoordinatorとして元のworktreeに残る。条件を一つでも満たせない場合は、この節の通常の報告規則に従う。ユーザーが`--execute`、terminal multiplexer、sub-agent handoffなど特定のhandoff手段を明示した場合は、このflowで置き換えず次段落の規則に従う。

ユーザーが一般commandの`--execute`、terminal multiplexer、またはsub-agent handoffを明示し、他に通常shellへの委譲条件がなければ、通常switch規則へ置き換えず公式Skillのhandoff workflowへ委譲する。

## 6. 通常fish shellへ委譲する

この節は、§4が委譲を要求し、かつ§2でherdr無効と判定した場合の案内方法。herdr有効と判定した後でもherdr CLIが利用できなくなった場合は、この節へフォールバックする。実行拒否の場合は§8に従い停止する。Agent内では、通常shell向けcommandを報告するだけで実行しない。新規作成とblocking copyが一つの依頼なら、途中のworktreeをAgentが先に作らず、作成、copy、Agent起動を最初から順に案内する。後続のblocking stepは前段成功時だけ進む形にする。

`pre-start` copyはblockingなので、switch成功後にAgentを起動できる。`post-start` copyはbackground/non-blockingという設定意図を尊重し、完了をAgent起動条件にしない。ユーザーがpost-start完了を明示的に必要とする場合は`pre-start`への移動を提案するが、project configとuser configのどちらも明示的な同意前には編集しない。

委譲workflowでAgent CLIがWorktrunk `--execute`に指定されていても、Worktrunk child shellはfishのSafehouse wrapperを読み込むとは限らない。Agent CLIの`--execute`をWorktrunk commandから外し、blocking step成功後に対話中のfishから`pi`、`claude`、`codex`、`opencode` wrapperを別commandで起動する。元の`--`以降にAgentへ渡す引数があれば、Worktrunk commandへ残さず、現在のclient helpに従ってshell-safeにAgent wrapper側へ移す。一般の非Agent `--execute`にはこの例外を広げない。自動multiplexer handoffは組み立てない。

blocking commandが作成後に失敗した場合はworkflowを停止してworktreeを残し、copyの自動retry、remove、rollback、Agent起動を行わない。診断が必要なら、提示済みのexit statusを使い、未提示ならそれを確認したうえで、秘密値を伏せたエラー周辺だけを依頼する。full hook logや環境変数値を貼るよう求めない。

## 7. 削除・交換後のsessionを扱う

この節はSafehouse内外に関わらず適用する。実行・委譲を問わず、`promote`、remove、merge cleanup、live pruneが現在のAgent worktreeを削除または入れ替える場合、command実行後は現在のsessionを継続しない。必要な作業は新しいAgent sessionから始める。対象が無関係なsibling worktreeだけなら現在のsessionは継続できる。

live pruneでは、Agent内のdry-run結果を候補として要約し、ユーザー確認を得てから、§3の削除・交換評価で実行先を決める。委譲が必要なら§2のherdr判定に従う。dry-run時の選択条件を保ち、確認前にlive実行済みとして扱わない。

## 8. sandbox拒否と結果を報告する

`Operation not permitted`や`deny(`に遭遇したら、失敗した操作と秘密値を伏せたエラーを報告して停止する。再試行、別経路での実行、policy変更、対象へのprobeは行わない。

結果では、環境判定（Safehouse内か外か、herdr有効か）、実行したWorktrunk commandの結果、検証済み絶対path、herdrで実行した操作と残したworkspace・pane、Agent内でもherdrでも実行せず通常shellへ案内したcommand、現在のsessionを継続できるか、新しいAgent sessionが必要かを簡潔に返す。project hookがない場合にsetupやbaseline testを推定しない。
