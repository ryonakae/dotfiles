# use-worktrunk への herdr 委譲・fork 自動化の追加 Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

Agent Safehouse 内のエージェントが `wt` で worktree を操作すると、sandbox 制限のため copy-ignored、remove、merge cleanup、live prune、grant 外への作成などが「通常 shell へのコマンド案内」に落ち、ユーザーが手でコマンドを打つ必要がある。fork も §5 の規則でコマンド報告止まりになる。Herdr 環境（`HERDR_ENV=1`）ではペイン内シェルが sandbox 外で動くことを検証済みであり、`herdr pane run` / `herdr agent start` を使えばエージェント自身がこれらを完遂できるが、その手順がスキル化されていない。

## Goal

`use-worktrunk` スキルが、herdr 環境では safehouse 制限下の wt 操作を herdr ペイン経由で（破壊的操作は承認後に）実行し、fork 意図のある依頼では新タブでの worktree 作成 → fork エージェント起動 → 引き継ぎ prompt 送信まで自動で完遂する。herdr がない環境では現行挙動を一切変えない。

## Out of Scope

- herdr 本体の `worktree` コマンド・`[worktrees]` 設定の利用（README の方針どおり使わない）
- worktrunk herdr plugin（`devashish2203/herdr-worktrunk`）の変更
- 公式 `worktrunk` スキル・外部 `herdr` スキルの変更
- safehouse ポリシー（`__safehouse_args.fish`、`local-overrides.sb`）の変更
- Zellij（`use-zellij`）への同等機能の追加
- 複数 fork の同時オーケストレーション機能（1 依頼 1 fork の完遂のみ）
- fork 対象 client の拡張（現行 §5 の pi / claude / codex / opencode の 4 種を維持）

## Requirements and Decisions

### Requirements

- **R1:** `HERDR_ENV=1` かつ herdr CLI が応答する場合、safehouse 内で §4 が「通常 shell へ委譲」としていた wt 操作を、herdr ペインでの実行に置き換える。§3 の境界分類・copy 評価は「Agent 内で実行できるか」の判定として維持し、不成立時の委譲先だけが変わる
- **R2:** 非破壊操作（worktree 作成・switch、copy-ignored、`wt merge --no-remove`、`wt step prune --dry-run`）は herdr で自動実行する。破壊的操作（`wt remove`、cleanup 付き `wt merge`、live `wt step prune`、`wt step promote`）は実行前にユーザー承認を取り、承認後にのみ herdr で実行する
- **R3:** `--yes` による approval 迂回禁止・force 系オプションの勝手な追加禁止は herdr 委譲でも維持する。ペイン内で wt が対話 approval を求めた場合、エージェント自身は応答しない
- **R4:** ユーザーが fork・引き継ぎの意図を示した依頼では、次を自動実行する: 現在 workspace に新タブを作成（`--cwd` はリポジトリルート、`--no-focus`）→ そのペインで `wt switch`（`--no-cd` を付けず、対話シェルの wt 関数で worktree へ cd を定着させる）→ 同ペインで `herdr agent start <name> --kind <kind> -- <fork 引数>` → `herdr agent prompt` で短い引き継ぎタスクを送信。`--wait` で初動は見届けず、起動と送信の完了を報告してコーディネーター（現セッション）は元の worktree に留まる。単なる worktree 作成依頼では fork しない
- **R5:** fork フローは safehouse 内外を問わず `HERDR_ENV=1` なら使う。safehouse 外では wt コマンド自体は従来どおり Agent 内で実行してよく、herdr は fork の配置と起動・指示出しにのみ使う
- **R6:** トポロジー: fork および fork なしの新規作成は「現在 workspace の新タブ」に実行して残す（plugin の対話フローと一致）。メンテナンス操作（copy 単体、remove、merge cleanup、prune、promote）は現在タブに `--no-focus` の一時ペインを split して実行し、成功時は出力を回収して報告した後にペインを閉じる
- **R7:** ペイン内で wt の承認プロンプトを検出したら、該当ペイン（またはタブ）をフォーカスしてユーザーに応答を委ね、その旨を報告して待つ。コマンド失敗時は出力を回収して報告し、ペインは診断用に残す。自動 retry・rollback・rollforward はしない
- **R8:** fork の session ID または client 種別を現行 §5 の規則（明示値・system context・信頼できる runtime metadata）で特定できない場合は自動 fork せず、現行どおり fork コマンドの報告に落とす。`HERDR_ENV=1` でも herdr CLI がエラーを返す場合は、現行の「通常 shell へのコマンド案内」へフォールバックする
- **R9:** `HERDR_ENV` が未設定または `1` 以外の環境では現行挙動を一切変えない。既存 evals（非 herdr 前提）の期待出力が成立し続ける
- **R10:** herdr の一般規則を尊重する: 対象指定は `--current`・明示 ID・一意な agent 名のみ、ID は JSON レスポンスから読む、自分が作っていないタブ・ペインは閉じない、`server stop` を実行しない

### Implementation Decisions

- **D1:** 新規スキルは作らず `use-worktrunk` を拡張する。herdr の具体的な操作手順・コマンド列・例外処理の詳細は `references/herdr-delegation.md` に分離し、SKILL.md には判定規則（いつ herdr 委譲になるか・承認の要否・フォールバック条件）と参照だけを書く。理由: wt 操作時に必ず読み込まれる既存トリガーを再利用し、委譲判断表の二重管理を避ける
- **D2:** ペイン内シェルは非 sandbox であることを検証済み（`APP_SANDBOX_CONTAINER_ID` 未設定、safehouse deny 対象の `~/.gnupg` が読める）。これは意図的な safehouse 迂回路なので、reference には「herdr ペインで実行してよいのは、このスキルが定める wt 操作と、その完了・状態確認に必要な読み取りだけ」という制限を明記する
- **D3:** agent 名とタブラベルは branch 名から導出し、herdr の名前制約 `[a-z][a-z0-9_-]{0,31}` へ正規化する。`herdr agent list` で衝突を確認し、衝突時はサフィックスで一意化する
- **D4:** ペイン内 wt コマンドの完了検知は、コマンド末尾に sentinel（例: `; echo __WT_DONE=$status`）を付けて `herdr pane wait-output --match` で待つ方式を基本とする。タイムアウト時は `pane read` で出力を確認し、承認プロンプトなら R7、失敗なら失敗処理へ分岐する
- **D5:** fork 引数の client 対応は §5 の 4 コマンドを `agent start --kind <kind> -- <args>` へ写像する（例: claude → `--kind claude -- --resume <session-id> --fork-session`）。実装時に `herdr agent`（kind 一覧）と各 client の現行 help を確認してから確定し、古い知識で組み立てない（§1 の既存規則を踏襲）

### Contracts

- SKILL.md frontmatter の `description` に herdr 環境での委譲・fork 完遂を追記する（トリガー精度に直結する公開コントラクト）
- §4 委譲表の各「通常 shell へ委譲」行は「herdr 利用可否 → 承認要否」の二段判定になる: herdr 可 + 非破壊 → herdr で自動実行 / herdr 可 + 破壊的 → 承認後 herdr で実行 / herdr 不可 → 現行どおり通常 shell へ案内
- fork フローの手順順序は R4 の記載順を固定とする（タブ作成 → wt switch → agent start → prompt 送信）。途中段の失敗で後続段へ進まない
- 状態遷移（fork フロー）: 各段の失敗時は R7/R8 に従い、作成済み worktree・タブは残す

## Current Context

### Confirmed

- この session は `HERDR_ENV=1` かつ safehouse 内。herdr ペイン内シェル（fish）は非 sandbox で、`wt v0.73.0` が実行できることをプローブで確認済み
- `herdr tab create [--workspace ID] [--cwd PATH] [--label TEXT] [--focus|--no-focus]`、`herdr pane split/run/read/wait-output/send-keys/close/focus`、`herdr agent start <name> --kind KIND --pane ID [-- <agent-args...>]`（kind に pi/claude/codex/opencode を含む）、`herdr agent prompt/wait/read/list` が現行 CLI に存在する
- `agent start` は「対話プロンプトにいる available shell pane」を要求し、レイアウトを作らない。既定 30 秒の起動タイムアウトを持つ
- worktrunk herdr plugin の対話フロー（picker.sh）は「新タブを開き、そのペインで `wt switch` を実行し、対話シェルの wt 関数が worktree へ cd して定着する」設計
- README の方針: herdr 本体の worktree 機能は使わない（`~/.herdr/worktrees` はテンプレート・hooks・copy が効かず safehouse allowlist 外）
- ペインは対話 fish なので、`claude`/`pi` 等は safehouse ラッパーの fish 関数として解決される（fork されたエージェントは通常どおり sandbox 内で起動する）
- `use-worktrunk` の実体は `config/.agents/skills/use-worktrunk/`（SKILL.md + evals/）。既存 evals は非 herdr 前提で、委譲時は「通常の対話 fish で実行するコマンドを案内する」ことを期待している
- 他の自作スキル（use-agent-safehouse、use-zellij 等）に `references/` ディレクトリの前例がある

### Assumptions

- `~/.agents/skills/use-worktrunk` はディレクトリ単位の symlink であり、references/ の新規ファイルは symlink 再作成なしで配布される（違った場合は `scripts/create-skills-symlink.sh` を再実行するだけで、外部挙動は変わらない）
- worktree の配置先（worktrunk の `worktree-path`）は safehouse allowlist 内（`~/Dev` 配下）にある。fork されたエージェントはそこを workdir として起動できる

## File Structure

- Create: `config/.agents/skills/use-worktrunk/references/herdr-delegation.md` — herdr 委譲・fork フローの具体手順、命名正規化、sentinel 待機、承認プロンプト・失敗時の処理、client→kind 写像
- Modify: `config/.agents/skills/use-worktrunk/SKILL.md` — frontmatter description、§2 への herdr 判定追加、§4 委譲表の二段判定化、§5 の herdr fork 自動化、§6 のフォールバック化、§7・§8 の整合
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json` — herdr 前提の eval を追加
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md` — herdr 環境 metadata の fixture 記述を追加

## Testing Decisions

- **Test seam:** スキルの evals（プロンプト → 期待出力・expectations）と、この session（herdr + safehouse）での実機シナリオ確認
- **Behavior:** (1) herdr 環境 metadata がある依頼で、非破壊の作成 + copy が herdr ペイン実行として扱われる (2) fork 意図のある依頼でタブ作成 → switch → agent start → prompt の手順が正しい順序・引数で示される (3) 破壊的操作で承認が先行する (4) 非 herdr 環境の既存 evals が変更なしで成立する
- **Prior art:** 既存 evals 1〜3 の形式（fixture metadata を信頼させ、「案内するコマンドは実行しない」と指示して手順を評価する）
- **Avoid:** eval から実 herdr サーバーへの依存。実機確認はこの session での手動シナリオに限定する

## Progress

- [ ] Task 1: references/herdr-delegation.md の作成
- [ ] Task 2: SKILL.md の改訂
- [ ] Task 3: evals の追加と既存 evals の整合確認
- [ ] Task 4: 実機シナリオ確認（この session で herdr 委譲の作成フローを実行）

## Tasks

### Task 1: references/herdr-delegation.md の作成

**Covers:** R2, R3, R4, R6, R7, R10, D2, D3, D4, D5

**Objective:** herdr 委譲と fork 自動化の実行手順が、SKILL.md から参照される単一の reference として存在する。

**Files:**
- Create: `config/.agents/skills/use-worktrunk/references/herdr-delegation.md`

**Dependencies:** なし

**Implementation notes:**
- 記述言語は既存 SKILL.md に合わせ日本語（コマンド・識別子は原文）
- 冒頭に有効化条件を明記: `test "$HERDR_ENV" = 1` が成立し、かつ herdr CLI の最初の呼び出し（例: `herdr pane current --current`）が成功すること。失敗時は SKILL.md §6 の通常 shell 案内へフォールバック（R8）
- ペインが非 sandbox である事実と、herdr ペインで実行してよい操作の制限（このスキルが定める wt 操作と完了・状態確認の読み取りのみ）を明記（D2）
- 手順を 3 系統で書く: (a) fork なし新規作成 = 新タブ（`tab create --cwd <リポジトリルート> --label <正規化名> --no-focus`）→ `pane run` で wt switch + sentinel → `wait-output` → 報告・タブは残す (b) fork あり = (a) の後、同ペインで `agent start` → `agent prompt`（`--wait` なし）→ 起動と送信の完了を報告 (c) メンテナンス操作 = 現在タブに `pane split --current --no-focus` → 実行 → `pane read` で出力回収 → 成功時のみ `pane close`
- (c) のうち破壊的操作（remove、cleanup 付き merge、live prune、promote）は実行前にユーザー承認を得る手順を明記。live prune は既存 §7 どおり dry-run 要約 → 確認 → live 実行の順を保つ（R2）
- 承認プロンプト検出（sentinel が来ないままタイムアウト → `pane read` で確認）→ `pane focus` または `tab focus` でユーザーへ委譲 → 応答後に再度 wait する分岐、および失敗時（sentinel の `$status` 非ゼロ）はペインを残して報告する分岐を書く（R7、D4）
- client→kind 写像と fork 引数は §5 の 4 client のみ。実装時に `herdr agent` の kind 一覧と各 client の現行 help を確認する規則を明記（D5）
- 命名正規化（`[a-z][a-z0-9_-]{0,31}`、`herdr agent list` での衝突確認とサフィックス付与）を書く（D3）
- ID は JSON レスポンス（`.result.tab`、`.result.root_pane`、`.result.pane.pane_id`）から読む。自分が作っていないタブ・ペインを閉じない（R10）
- fork 後に現セッションの worktree が削除される操作とは独立であること（§7 の session 継続規則は変更しない）

**Test cases:**
- reference 単体を読んだ実装者が、fork あり依頼の 4 段手順（タブ作成 → switch → agent start → prompt）を、失敗時の停止位置込みで再現できる → 手順の欠落・順序曖昧がない
- 破壊的操作の節に「承認前に実行しない」が明記されている → grep で確認可能

**Complete when:**
- 上記 3 系統の手順、例外分岐、命名規則、写像表がすべて記載されている
- SKILL.md 側で定義する判定規則（いつ herdr 委譲になるか）と重複していない（手順のみを持つ）

**Validation:**
- Run: `grep -l "HERDR_ENV" config/.agents/skills/use-worktrunk/references/herdr-delegation.md && grep -c "承認" config/.agents/skills/use-worktrunk/references/herdr-delegation.md`
- Expected: ファイルパスが出力され、承認への言及が 1 件以上ある

### Task 2: SKILL.md の改訂

**Covers:** R1, R2, R4, R5, R8, R9, D1, Contracts

**Objective:** SKILL.md が herdr 環境の判定と委譲先の切り替えを定義し、herdr 非対応環境では現行の記述内容が変わらない。

**Files:**
- Modify: `config/.agents/skills/use-worktrunk/SKILL.md`

**Dependencies:** Task 1（reference のファイル名・節構成を参照するため）

**Implementation notes:**
- frontmatter `description` に herdr 環境での委譲・fork 完遂を追記（1〜2 句に留め、既存のトリガー記述を壊さない）
- §2 の環境判定に herdr 判定を追加: safehouse 判定と独立に `HERDR_ENV` を確認し、結果を session で再利用する。「safehouse 内 × herdr 有」「safehouse 内 × herdr 無」「safehouse 外 × herdr 有」「safehouse 外 × herdr 無」の 4 象限で、変わるのは委譲先（herdr か通常 shell 案内か）と fork の完遂可否だけであることを明記（R1、R5、R9）
- §4 の表は行を増やすのではなく、「通常 shell へ委譲」の意味を「herdr 利用可なら references/herdr-delegation.md の手順で実行（破壊的操作は承認後）、不可なら §6 の案内」と再定義する注記を表の前後に置く。表自体の操作分類（何が Agent 内で可能か）は変更しない（R1、R2）
- §5 に「herdr 環境では fork 意図のある依頼に限り reference の fork フローで完遂する」分岐を追加。session ID / client を特定できない場合は現行の報告へ落とす既存文をフォールバックとして残す（R4、R8）
- §6 は「herdr 不可時のフォールバック」と位置づけを変えるが、案内手順の内容自体は変更しない（R9）
- §8 の報告項目に「herdr ペインで実行した操作と、作成・残置したタブ / ペイン」を追加
- 既存の規則文（`--yes` 迂回禁止、force 追加禁止、§3 の境界分類、§7 の session 継続規則）は変更しない

**Test cases:**
- `HERDR_ENV` 未設定のシナリオを SKILL.md だけで辿ると、現行と同じ結論（通常 shell 案内・fork コマンド報告）に到達する → 既存 evals 1〜3 の期待出力と矛盾しない
- safehouse 外 × herdr 有のシナリオで、wt は Agent 内実行・fork は herdr 完遂と読める（R5）

**Complete when:**
- 4 象限すべての挙動が SKILL.md から一意に導ける
- reference への参照パスが正しい
- 既存 evals の期待出力と矛盾する記述がない

**Validation:**
- Run: `grep -n "HERDR_ENV\|herdr-delegation" config/.agents/skills/use-worktrunk/SKILL.md`
- Expected: §2 相当の判定と reference 参照が出力される

### Task 3: evals の追加と既存 evals の整合確認

**Covers:** R2, R4, R9

**Objective:** herdr 前提の挙動が evals で検証可能になり、既存 evals は変更なしで成立し続ける。

**Files:**
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md`

**Dependencies:** Task 2

**Implementation notes:**
- 既存 evals の形式に合わせ、fixture metadata で環境を宣言し「案内・実行するコマンド自体は実行しない」と指示して手順を評価する（実 herdr サーバーへ依存しない）
- 追加する eval は 2 件: (1) herdr + safehouse で fork 意図のある依頼 → タブ作成 → wt switch → agent start（正しい kind と fork 引数）→ prompt 送信の順序、`--wait` を使わないこと、コーディネーターが元 worktree に留まることを expectations にする (2) herdr + safehouse で `wt remove` 依頼 → 実行前にユーザー承認を求め、承認なしで herdr 実行しないことを expectations にする
- 既存 evals 1〜3 は prompt・expectations とも変更しない。fixtures.md には herdr 環境用の metadata 節を追加し、既存 fixture の記述は変えない

**Test cases:**
- `jq . evals.json` が成功する → JSON として妥当
- 既存 eval の diff が空（id 1〜既存最終の変更なし）→ R9 の担保

**Complete when:**
- 追加 2 件が既存形式（prompt / expected_output / files / expectations）を満たす
- 既存 evals に変更がない

**Validation:**
- Run: `jq -e '.evals | length' config/.agents/skills/use-worktrunk/evals/evals.json && git diff --stat config/.agents/skills/use-worktrunk/evals/`
- Expected: eval 件数が現行 +2 になり、diff は追加分のみ

### Task 4: 実機シナリオ確認

**Covers:** R1, R2, R4, R6, R8（実機での成立確認）

**Objective:** この session（herdr + safehouse）で、改訂後スキルの手順どおりに fork なし新規作成フローが完遂することを確認する。

**Files:**
- なし（scratchpad 配下の使い捨てリポジトリで実施）

**Dependencies:** Task 1, Task 2

**Implementation notes:**
- scratchpad に使い捨て git リポジトリを作り、reference の手順どおり `tab create --no-focus` → `pane run` で `wt switch -c <branch>` + sentinel → `wait-output` → 結果報告まで実行する
- fork フロー（agent start）は実エージェントの起動とトークン消費を伴うため、実行はユーザーが明示的に求めた場合のみとし、既定では作成フローの確認に留める
- 確認後、作成したタブ・worktree・使い捨てリポジトリを片付ける（自分が作ったものだけを閉じる・消す）

**Test cases:**
- 新タブのペインで wt switch が成功し、sentinel `__WT_DONE=0` が `wait-output` で取れる → herdr 委譲の作成フローが成立
- ペインの cwd が worktree へ移っている（`pane get` の cwd）→ cd 定着の確認

**Complete when:**
- 上記 2 点が確認でき、後片付けが完了している

**Validation:**
- Run: reference 記載の手順（tab create → pane run → wait-output → pane get）
- Expected: sentinel が status 0 で一致し、ペイン cwd が新 worktree の絶対パス

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1 | Task 2, 4 | SKILL.md の 4 象限記述、実機での委譲実行 |
| R2 | Task 1, 2, 3 | reference の承認手順、eval (2) の expectations |
| R3 | Task 1 | 承認プロンプト非応答の明記を grep で確認 |
| R4 | Task 1, 2, 3 | fork 4 段手順の記載、eval (1) の expectations |
| R5 | Task 2 | safehouse 外 × herdr 有のシナリオ記述 |
| R6 | Task 1, 4 | 3 系統トポロジーの記載、実機でのタブ残置確認 |
| R7 | Task 1 | 承認プロンプト・失敗分岐の記載 |
| R8 | Task 1, 2 | フォールバック条件の記載（reference 冒頭と §5） |
| R9 | Task 2, 3 | 既存 evals 無変更、非 herdr シナリオの結論不変 |
| R10 | Task 1 | ID の JSON 取得・close 制限の記載 |
| D1 | Task 1, 2 | 判定は SKILL.md・手順は reference の分離 |
| D2 | Task 1 | ペイン実行の制限の明記 |
| D3 | Task 1 | 命名正規化規則の記載 |
| D4 | Task 1, 4 | sentinel 方式の記載と実機動作 |
| D5 | Task 1 | 写像表と実装時 help 確認規則の記載 |

## Final Validation

- [ ] `jq -e '.evals | length' config/.agents/skills/use-worktrunk/evals/evals.json` — Expected: 現行件数 +2、exit 0
- [ ] `git diff config/.agents/skills/use-worktrunk/evals/evals.json` — Expected: 既存 eval エントリに変更がなく、追加のみ
- [ ] `grep -n "HERDR_ENV" config/.agents/skills/use-worktrunk/SKILL.md config/.agents/skills/use-worktrunk/references/herdr-delegation.md` — Expected: 両ファイルに判定・有効化条件が存在
- [ ] `ls -la ~/.agents/skills/use-worktrunk ~/.claude/skills/use-worktrunk` — Expected: dotfiles の実体を指す symlink で、references/ が配布されている（per-file symlink だった場合は `sh scripts/create-skills-symlink.sh` を実行して再確認）
- [ ] Task 4 の実機シナリオ（tab create → pane run → wait-output → pane get → 後片付け）が成功
- [ ] Requirement Coverage に未対応項目がない
- [ ] 計画と実際の変更内容が整合している
- [ ] 上記のすべてが成功した後、計画を同名のまま `docs/plans/archived/` へ移した

## Risks and Open Questions

- `herdr agent start` の kind 別起動コマンドが fish ラッパー関数を経由するかは claude / pi で実績があるが、codex / opencode は未確認。実装時（D5 の help 確認）で差異が見つかったら、その client の fork は現行どおり報告へ落とす
- sentinel 方式は対話シェルのプロンプト描画と干渉しうる（今回のプローブでも入力混線が 1 度発生）。reference には「`pane run` は前のコマンドが完了しプロンプトにいることを確認してから実行する」旨を含める
- wt の承認プロンプトの文言・描画は wt のバージョンで変わりうるため、検出は「sentinel が来ない + pane read の内容確認」で行い、特定の文字列一致に依存させない
- 未解決事項: なし
