# t3-worktree・t3-merge スキル Implementation Plan

## Requirements

c-41 の `c41-worktree`・`c41-merge` が持つ「T3 Code で worktree を作成し、PR・マージ・片付けまで行う」フローを、どのリポジトリでも使える自作スキルにする。決定の経緯と理由は [dig log](../dig/2026-11-26-t3-worktree-merge-skills.md) にある。

- `config/.agents/skills/` に `t3-worktree`・`t3-merge` を新設し、`use-t3-code` からリンクする。
- 作業場所の判断は `use-t3-code` 本体で行い、現在の場所に倒す。worktree を作るまでもない作業では提案しない。
- worktree の作成は、理由・基点・ブランチ名を提示し、ユーザーの承認後に行う。
- リポジトリごとの違いは、新しい記述規約を設けず、T3 のプロジェクト設定・Git・GitHub の状態から判定する。
- リポジトリが作業場所・マージの手順を独自に持つ場合（スキル、AGENTS.md の記述など形式を問わない）は、そちらを優先する。
- 特定の種類のリポジトリに固有の内容（iOS の配信、Simulator など）を汎用スキルに書かない。

対象外:

- c-41 リポジトリの編集。別スレッドで行う（末尾「c-41 側の後続作業」）。
- 準備スクリプト本体の汎用提供。内容がリポジトリ固有のため、各リポジトリで作成する。
- 他のリポジトリから汎用スキルを名前で参照させる仕組み。

## Implementation Decisions

「レビューで補った判断」と記した項目は、dig log の決定を具体化するために Plan の独立レビューを受けて足したもの。Plan の承認で確定する。

### use-t3-code: 作業場所の判断

「最初にサブエージェントへの委譲を判断する」の次に節を足し、依頼の開始時と、調査から変更へ広がった時点で判断させる。

| 依頼 | 作業場所 |
|---|---|
| 質問への回答、読取調査、レビュー、計測 | 現在の場所 |
| 誤字・リンク・設定値など、内容と影響が明確で局所的な修正 | 現在の場所 |
| 判断に迷う中間の作業（1ファイルで完結する不具合修正、依存1件の更新、小さな UI 調整など） | 現在の場所 |
| 同じ依頼の続き、レビュー指摘の修正 | その依頼の場所を継続 |
| dig・Plan に進む変更、複数の commit に分かれる規模の変更、PR でのレビューや確認が要る変更 | `t3-worktree` を読み、新しい worktree を提案 |

- 例外: 現在の場所に他の作業の未コミット変更がある、または他のスレッドが同じ checkout で作業中なら、規模にかかわらず `t3-worktree` を読む。
- 優先順位（レビューで補った判断）: ユーザーの作業場所の指定 → リポジトリ独自の手順 → プロジェクト設定（`t3-worktree` の手順2）→ 上の例外 → 表。
- 資料の表に `t3-worktree`（worktree の提案・作成・初期整備）と `t3-merge`（PR 作成・マージ・片付け）を足す。`references/worktree.md` の行は `t3-worktree` へ置き換え、ファイルは削除する。frontmatter の description と `agents/openai.yaml` の説明も、判断を扱う旨に合わせる。

### t3-worktree

worktree を提案すると判断した後の手順だけを持つ。判断表は書かない。

1. **現在地の確認**: `t3_worktree_status` と `git status --short`。すでに今回の依頼の worktree なら続ける。別の依頼の worktree に紐付いている場合、`t3_worktree_handoff` は失敗するので、新規スレッドが必要な旨を説明する。
2. **プロジェクト設定の確認**: `t3_project_read`。
   - `defaultThreadEnvMode` が `local`: ユーザーが worktree を明示していない限り提案せず、現在の場所で進める。他の作業の未コミット変更があれば混ぜず、重なって安全に分けられない箇所だけ確認する。
   - 未設定、または `worktree` なのにスレッドが worktree に紐付いていない: 続ける。
   - `runOnWorktreeCreate` のスクリプトがあれば整備済み。
3. **未登録のときの兆候確認**: 依存の lockfile、primary checkout に実在する Git 除外ファイルの名前（`.env`、証明書など。中身は読まない）、`.gitattributes` の LFS 指定。兆候がなければ準備不要として進める。兆候があれば未整備。
4. **基点とブランチ名の決定**:
   - 独立した依頼は `origin` の既定ブランチ。`git symbolic-ref --short refs/remotes/origin/HEAD` で検出し、得られなければ `gh repo view --json defaultBranchRef` で確かめる。未マージの作業ブランチを前提とする続きは、そのブランチ。リモートがなければローカルの現在のブランチ。一意に決まらなければユーザーに確認する（レビューで補った判断）。
   - ブランチ名は目的に合う短い名前（`feat/...`、`fix/...` など）。リポジトリの既存ブランチの命名に合わせ、衝突したら別名にする。
5. **提案と承認**: 理由・基点・ブランチ名を示して承認を待つ。確認中は読取調査までにとどめる。未整備なら、同じ提案の中で初期整備の内容も示し、worktree の作成と整備を別々に承認できるようにする。
   - ユーザーがその依頼で worktree を明示している場合は、作成は承認済みとして扱い、基点とブランチ名を示してそのまま進める（レビューで補った判断。c-41 の現行規則と同じ）。初期整備の承認は別に要る。
6. **初期整備（未整備で、承認されたとき）**: 「今回は準備なしで進める」も選べる。
   - 内容: 準備スクリプトの作成（リポジトリに既存のものがあれば使う）、既定ブランチへの commit・push、`t3_project_update` での登録（`runOnWorktreeCreate: true`）、GitHub のマージ時ブランチ自動削除が無効なら有効化。既定ブランチへ直接 push する点、T3 の設定と GitHub の設定を変える点は、提案に項目ごとに明示する。
   - 現在の場所で整備してよい条件（レビューで補った判断）: 既定ブランチにいて、他の作業の未コミット変更がなく、開始前からの未 push コミットがない。満たさなければ現在の場所では整備せず、準備なしで進めるか、整備を先に別の依頼として行うかを確認する。push するのは整備の commit だけ。
   - handoff の基点に準備スクリプトが存在することを確かめてから登録と handoff へ進む。未マージの作業ブランチが基点でスクリプトがなければ、準備は移動後に手動で行う旨を伝える。
   - `t3_project_update` の `scripts` は配列全体を渡すため、既存のスクリプトを残して足す。
   - Git 除外ファイルをコピーするスクリプトにする場合は、対象のファイル名を提案に列挙して承認を得る。対象は Git 除外されている通常ファイルに限り、既存ファイルを上書きせず、中身を出力しない。
7. **handoff**: `t3_worktree_handoff` をそのターン最後のツール呼び出しにする。`branch`、`baseRef`、`startFromOrigin`（`origin` のブランチが基点なら `true`、ローカルのブランチが基点なら `false`）、`continuationPrompt`（元の依頼、確定した判断、次の作業、参照文書、必要なローカル資料の絶対パス）。
   - 未コミット変更は移動先へコピーされない。stash・commit・上書きで運ばず、土台に要る場合は移し方を先に確認する。秘密の値を継続プロンプトに書かない。
8. **移動後**: 返されたパス・ブランチ・`startedFromOrigin` を確認し、準備スクリプトの完了を確かめてから再開する。失敗を残したまま実装を始めず、原因を報告する。

`references/worktree.md` の内容（`git worktree` や内蔵の worktree 機能を使わない、別スレッド・子タスクは `t3_thread_launch` の `workspaceStrategy`・`delegate_task` の `isolation`、削除は `storageCleanup` に任せる）をここへ移す。worktree 作成に push・PR・マージ・削除は含めない。

### t3-merge

ユーザーが PR の作成またはマージを明示的に頼んだときだけ使い、完了報告では提案しない。失敗したらそこで止めて報告する。`defaultThreadEnvMode` が `local` のリポジトリでも、明示的に頼まれたらこの手順で行う。リモートや GitHub がなく PR を作れない場合は、その旨を伝える。PR の作成・マージ・紐付け・watch に使うツールは、T3 が注入する指示に従う。

依頼ごとの範囲（レビューで補った判断）:

| 依頼 | 行う段階 |
|---|---|
| commit だけ、commit と push だけ | このスキルを使わない。`commit-push` に任せ、ブランチを切らない |
| PR を作って | 1〜3 |
| PR を作ってマージして | 1〜7 |
| 既存の PR をマージして | 対象の PR を確かめ、未コミット変更や未 push の commit がなければ 4〜7 |

1. **ブランチの決定**: `t3_worktree_status` と `git status --short`。既定ブランチにいれば作業ブランチを切る。worktree にいれば今のブランチのまま進め、T3 の自動名でも変えない。
2. **commit・push**: 未コミット変更があれば `commit-push` スキルの手順。作業ツリーがきれいで未 push の commit だけがあれば、それを push する。push はローカルと同じ名前のリモートブランチへ行い、upstream を設定する（T3 は同名の PR のマージで worktree を片付けるため）。
3. **PR の作成**: 開いている PR は、head のリポジトリ・ブランチと基点がすべて一致するものだけ再利用する。基点は、worktree の作成元のブランチ、または作業ブランチを切った元のブランチ。タイトルは直近のマージ済み PR の形式と言語に合わせ、履歴がなければ `commit-push` のコミットメッセージ規則。本文は PR テンプレートがあればそれ、なければ「変更」「確認」の2見出し。末尾に attribution。PR はスレッドに紐付ける。
4. **マージ**: mergeable とチェックの状態を確認する。
   - コンフリクト、チェックの失敗、レビューの要求が一つでもある: 報告して止める。`--admin` や強制 push は使わない。
   - 上がなく、チェックが待ち・実行中: マージせず PR を watch して手を返す。
   - マージできる: 基点ブランチの直近のマージ済み PR と同じ方式。履歴がなければ `--merge`。その方式がリポジトリで無効、または判別できないときは、許可されている方式が一つならそれを使い、複数ならユーザーに確認する（レビューで補った判断）。
   - primary checkout で作業していた場合は、基点ブランチへ戻して `git pull --ff-only` する。
5. **ブランチの削除**: 対象は、この PR の作業ブランチと、このスレッドの子タスクが作ったブランチに限る。既定ブランチ、PR の基点、`develop` などの常設ブランチ、どこかの worktree で使用中のブランチは消さない。
   - リモート: GitHub の自動削除が無効なら、マージした PR の作業ブランチを消す。
   - ローカル: primary checkout で `git fetch --prune` し、追跡先が消えていて PR の基点に取り込み済みのブランチを `git branch -d` で消す。今のスレッドのブランチは worktree で使用中なので残り、T3 が worktree を片付けた後、次にこのスキルを使ったときに消える（レビューで補った判断: 取り込み済みというだけでは消さず、追跡先が消えたことを条件に足す）。
6. **付随物の片付け**: `use-t3-code` の `references/thread-lifecycle.md`「付随物を片付ける」に従う。同資料の子ブランチの取り込み判定は `main` 固定ではなく PR の基点で行うよう、記述を直す。
7. **報告**: PR の URL、merge commit、消したもの、残したものとその理由。自動削除が無効のままなら、有効化の提案を1行添える。

注意として次を書く。

- スレッドの settle と worktree の削除は含めず、T3 Code に任せる。
- リポジトリの指示が段階を置換・追加する場合はそちらに従う。
- T3 はマージ時に worktree を削除する。マージ後に実行する処理があるリポジトリは、worktree が消えても成立する形（マージと同一コマンドへの連結、primary checkout からの実行など）を、そのリポジトリの手順で定める（レビューで補った判断: 汎用スキルは方式を固定せず、制約だけを伝える）。

### 共通

- 既存の自作スキルに合わせ、本文は日本語、各スキルに `agents/openai.yaml` を置く。`t3-merge` は明示依頼でだけ使うため、`commit-push` と同じく `allow_implicit_invocation: false` にする。
- T3 のツールの引数や戻り値の説明は、T3 が注入する指示とツール定義に任せ、スキルには判断と順序だけを書く（`use-t3-code` の役割分担と同じ）。
- 自作スキルは mise の glob で配置されるため、`mise.default.toml` の変更は要らない。新しいスキルディレクトリのリンク作成には apply が要る。

## Tasks

review の base commit: `f89cd70`

- [x] **t3-worktree**: `config/.agents/skills/t3-worktree/SKILL.md` と `agents/openai.yaml` を作成する。
- [x] **t3-merge**: `config/.agents/skills/t3-merge/SKILL.md` と `agents/openai.yaml` を作成する。
- [x] **use-t3-code**: `config/.agents/skills/use-t3-code/SKILL.md` に作業場所の判断の節とリンクを足し、description と `agents/openai.yaml` を合わせ、`references/worktree.md` を削除する。`references/thread-lifecycle.md` の子ブランチの取り込み判定を PR の基点に直す。
  - `references/thread-lifecycle.md` の worktree の項は T3 の `storageCleanup` に任せる旨のまま残す。

## Final Validation

push 前に行う。実 HOME への apply と T3 の設定変更は含めない。

- [x] スキルの形式: 2つの `SKILL.md` の frontmatter の `name` がディレクトリ名と一致し、description が起動条件を述べている → 一致する。
- [x] リンクと参照: `config/.agents/skills/` の `SKILL.md` と `references/` の相対リンクがすべて実在のファイル・見出しを指し、削除した `references/worktree.md` へのリンクが現行のスキル・文書に残っていない（`rg -n 'references/worktree.md' config .agents README.md CLAUDE.md` → 該当なし。`docs/dig/`・`docs/plans/` の記録は対象外）。
- [x] ツールとの整合: スキルに書いたツール名と引数名（`t3_worktree_status`、`t3_worktree_handoff`、`t3_project_read`、`t3_project_update`）を ToolSearch で得た定義と照合する → 矛盾がない。
- [ ] 決定との整合: dig log の決定事項を1件ずつスキルの記述と照合する → 抜け・矛盾がない。iOS・TestFlight・Simulator・c-41 固有の語が `t3-worktree`・`t3-merge` にない。
- [ ] 分岐の読み合わせ: 次の場面でスキルの記述をたどり、期待する操作と停止点になることを確かめる。恒久テストは作らない。
  - commit だけの依頼を既定ブランチで受けた → `t3-merge` を使わず、ブランチを切らない。
  - 既存 PR のマージだけの依頼 → commit・push を行わず 4 から始まる。
  - `defaultThreadEnvMode` が `local` で、他の作業の未コミット変更がある → 提案せず、変更を混ぜない。
  - 未整備で、現在の場所に他の作業の未コミット変更がある → 現在の場所では整備しない。
  - 準備スクリプトが失敗した → 実装を始めず報告する。
  - チェックの待ちと失敗が併存する → マージも watch もせず報告して止まる。
  - 別 fork に同名ブランチの PR がある → 再利用しない。
- [x] 差分: `git diff --check` → 出力なし。
- [x] 配置予定: `mise -C ~/dotfiles -E <この PC の構成> dot apply --dry-run` → `~/.agents/skills/` と `~/.claude/skills/` の `t3-worktree`・`t3-merge` の4件のリンク作成だけ。`default,work`・`default,private` の両方で4件だけを確認。

## push 後の作業（Plan の完了後、それぞれ承認を得て行う）

実機への反映は Plan の承認に含めない。push の後、PC ごとに内容を示して承認を得る。

- **この PC**: apply して4件のリンクが正本を指すことを確認する。`t3_project_update` で dotfiles プロジェクトの `defaultThreadEnvMode` を `local` にし、`t3_project_read` で確かめる。
- **別 PC**: [Linked environment 手順](../../config/.agents/skills/use-t3-code/references/linked-environments.md)で pull・apply し、同じ2点を確認・設定する。接続不能や未コミット変更との衝突があれば止めて報告する。

## c-41 側の後続作業（この Plan の対象外）

c-41 には dotfiles のグローバル設定への依存を持たせない。`c41-worktree`・`c41-merge` は全文を持つ独立したスキルとして維持し、汎用スキルを参照させない。c-41 のスレッドで次だけ行う。

- グローバルスキルへの参照3件を、スキル名・ファイル名の指定から行為の記述へ変える。
  - `c41-merge`: 「`commit-push` スキルの手順で行う」→「commit して push する」
  - `c41-merge`: 「`use-t3-code` の `references/thread-lifecycle.md` に従う」→「子スレッド・ブランチを片付ける」
  - `c41-worktree`: 「`use-t3-code` と、その `references/worktree.md` を読む」→ 削除

`references/worktree.md` の削除から c-41 側の修正までの間、`c41-worktree` の参照は切れる。T3 のツールで worktree を扱う旨は `c41-worktree` の本文にあるため、順序の制約は設けない。

---

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
