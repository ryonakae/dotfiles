# use-t3-code ハイブリッド委譲・モデル非依存化 Implementation Plan

## Requirements

`config/.agents/skills/use-t3-code/` を、メインモデル変更時にスキル本体の改修が不要なハイブリッド運用へ改修する。

- **ハイブリッド運用**: 原則として現在起動中の親モデルで作業を完結させ、ハンドオフ負荷を上回る利益がある場合のみサブエージェントへ委譲する。
- **2 層分離**: 不変ルール層（`SKILL.md`・`references/delegation.md`）から具体モデル名・モデル ID・版数を排除し、可変モデル層（`references/models.md`、`model-benchmarks.md` から改名・再構成）1 ファイルへ集約する。
- **委譲時のモデル選定**: 委譲すると判断した場合、委譲先を親と同一モデルに固定・制限しない。プロバイダ別の使用量枠の節約・分散も含め、`references/models.md` からティア・用途・別系統の基準でモデルを選定する。選定の結果として親と同一モデル・同一オプションになった場合のみ内蔵サブエージェントを使用する。
- **軽量ティア委譲の維持**: 範囲と手順を依頼文に書け、結果を機械的に確かめられる探索・確認を軽量ティアへ逃がす運用（速度・費用・使用量枠節約）を維持する。
- **読者向け文章の優先方針**: 不変層では `models.md` の文章スロットを参照する形に一般化し、親が文章スロットの系統なら直接執筆する。文章スロット内では「構成・論旨の判断を伴う新規作成や長文は Neon、短い UI 文言・局所的な推敲は Hydrogen」とし、指標由来ではなくユーザー評価に基づくため自動更新対象外とする。
- **更新の再現性**: `models.md` は全 effort 網羅表を廃止しつつ、将来のモデル更新時に現行代表モデルと新モデルを同条件で再比較できる最小限の基準と手順を保持する。
- **他スキルとの役割分担**: レビュー要否の判断は `plan`・`implement` を正本とし、`use-t3-code` は委譲先とモデル選定のみを規定する。
- **環境前提**: private / work の各 Mac で有効なプロバイダは共通のため、マシン間のプロバイダ差分対応は設けない。

対象外:

- `plan`・`implement`・`t3-worktree`・`t3-merge` スキル本体の変更。
- `agents/openai.yaml` の変更（汎用表現のため変更不要）。
- ベンチマーク値の今回時点での再計測（現行 `model-benchmarks.md` の確認済みデータから代表設定を抜粋して移行する）。

## Implementation Decisions

### 1. 不変層と可変層の境界

- **排除対象**: モデル名・モデル ID・版数。系統名（Claude・GPT・Gemini）とプロバイダ名（Codex・Claude・Antigravity）は「別系統」やプロバイダ固有制約の記述に必要なため不変層に残す。
- **改名**: `references/model-benchmarks.md` は網羅ベンチマーク集から選定表＋更新手順へ役割が変わるため、`references/models.md` へ改名し旧ファイルを削除する。

### 2. `SKILL.md`（不変層）

- frontmatter の description から「積極的な委譲」のニュアンスをハイブリッド方針に合わせて調整する。
- 「最初にサブエージェントへの委譲を判断する」を「原則は親モデルで完結し、以下の発動条件に該当する場合のみ委譲する」へ反転する。ハーネス既定を上書きする文言を削除する。
- 発動条件は主観的な表現だけにせず、観測可能な条件を箇条書きで明記する:
  1. **独立レビュー**: `plan`・`implement` の必須レビュー条件（要否は各スキルを正本とする）、またはそれらを使わない通常作業での数行を超える差分の完了報告前。
  2. **コンテクスト保護・並列化**: 読む対象を事前に特定できない横断探索、互いに依存しないまとまった並列作業。
  3. **局所難所への上方委譲**: 親が最上位ティアでない場合に、依頼文へ切り出せる難所（原因調査・設計案検証・局所的な難実装）を上位ティアへ任せる。作業全体が難所（方針・範囲ともに未確定）なら子へ投げず、親モデルの切り替えをユーザーへ提案する。
  4. **速度・費用・枠節約**: 範囲と手順を依頼文に書け、結果を機械的に確かめられる探索・確認を軽量ティアへ任せる。
  5. **読者向け文章**: 親が文章スロットの系統でない場合の文言案作成・推敲。
- 「サブエージェントの既定モデル・思考レベル」節の具体モデル表を削除し、`references/delegation.md` と `references/models.md` への参照のみに簡潔化する。
- 資料表の `references/model-benchmarks.md` へのリンクを `references/models.md` へ更新する。

### 3. `references/delegation.md`（不変層）

- **選定フローの簡素化**:
  1. 発動条件と難度 4 問（モデル非依存のため維持）で委譲要否・ティア（軽量／標準／最上位）・別系統の要否を決める。
  2. `references/models.md` のモデル表から該当ティア・用途（および使用量枠分散・別系統）に合うモデルと開始 effort を選ぶ。親モデル固定の制限は設けない。
  3. 親自身のティアは `models.md` で確認し、親がすでに最上位ティアなら上方委譲は行わない。
  4. 選定の結果、親と同一プロバイダ・同一モデル・同一オプションになった場合のみ内蔵サブエージェントを使用する。それ以外は `delegate_task` で明示指定する。
  5. `models.md` に記載のモデル ID が `orchestrator_capabilities` で利用不能（消失）な場合は、無断で別モデルへ切り替えず `models.md` の更新を提案する。必須の独立レビュー（`implement` 等）は親が代行せず、無断で別モデルへも切り替えず、代替先（利用可能な別モデル、または親と同一モデルの独立コンテクスト）をユーザーへ確認する。
  6. 結果が不足する場合の引き上げ（手順 5）は維持する。
- **読者向け文章の優先方針**: 具体モデル名を外し「`models.md` の文章スロットを使用する。親が同系統なら直接執筆する」へ一般化する。Antigravity の `runtimeMode` 制約（`approval-required` 既定・文言案返却のみ・反映は親が担当）はプロバイダ固有制約として維持する。
- **移動**: 日付付きのモデル ID 対応表・JSON 指定例（104–133 行）、および作業種別と指標の対応・隣接 effort 比較などのベンチマーク選定手順（61–69 行、84–99 行）は実行手順から削除し、`models.md` のモデル表・更新手順へ移動する。

### 4. `references/models.md`（可変層・数十行の 3 部構成）

1. **モデル表（実行時参照）**:
   - 現行の採用モデルと親になり得るモデルを掲載する（`gpt-6-luna`, `gpt-6.1-terra`, `gpt-6.2-sol`, `gpt-6.2-astra`, `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-2`, `gemini-4-neon`, `gemini-4-hydrogen`）。`gemini-4-carbon`, `gemini-4-argon` は除外。
   - 列: `providerInstanceId`、`model`、系統、ティア（軽量／標準／最上位）、effort の option 名、effort（既定／引き上げ先／打ち止め）、根拠 1 行（決定記録）、確認日。
   - 最小限の `delegate_task` 指定例（JSON）と、速度系 option・根拠のない思考レベルを無断指定しない注意をここへ移す。
2. **文章スロット**:
   - Gemini 系の 2 モデルと使い分け基準: 構成・論旨の判断を伴う新規作成や長文は `gemini-4-neon`、短い UI 文言・局所的な推敲は `gemini-4-hydrogen`。
   - 「ユーザー評価に基づくため、ベンチマーク指標では自動更新せずユーザー判断でのみ変更する」旨を明記する。
3. **更新手順（更新時のみ参照）**:
   - 参照元（Artificial Analysis）と取得 URL の規則・列順の注意（現行 `model-benchmarks.md` 138 行のノウハウを保持）。
   - 作業種別と重視指標の対応（リポジトリ変更＝FrontierCode、環境操作＝Terminal-Bench、資料読解＝GDP.pdf、補助＝AutomationBench・AA-Briefcase）。
   - ぶれ幅の算出式（二項分布 95% 区間の半幅概算）とティア境界（価格比）の規則。
   - 計測条件の注意（Codex・Claude Code ハーネス評価とモデル単体評価の区別、Antigravity 経由の実測ではない点）。
   - effort 引き上げ基準（隣接 effort でぶれ幅を超える伸びがある場合のみ引き上げ、頭打ちを打ち止め列へ記録）。
   - **比較ルール**: 保存した根拠値は決定記録であり、指標の版が変わるため次回更新時の直接比較に使わない。更新時は**現行代表モデルも同日に同一比較ページから再取得して新モデルと比較する**。
   - 更新契機: ユーザーからの更新依頼、または `orchestrator_capabilities` での表記載 ID の消失（利用不能）の検知時。

## Tasks

- Base commit: `7069bc02db9bbfbf3d06c2826f2705202eebfc4c`

- [x] `config/.agents/skills/use-t3-code/references/models.md` を作成し、`config/.agents/skills/use-t3-code/references/model-benchmarks.md` を削除する。
  - 現行 `model-benchmarks.md` の確認済みデータ（2026-11-18 / 2026-11-25 確認分）から採用モデル・effort（既定／引き上げ先／打ち止め）・根拠 1 行を正確に転記し、URL 規則・ぶれ幅算出式・ティア境界規則・計測注意を落とさない。
  - `delegation.md` から移動する指定例（JSON）と option 注意事項を統合する。
- [x] `config/.agents/skills/use-t3-code/references/delegation.md` を不変層ルールへ更新する。
  - モデル名・ID・版数を完全に除去し、ハイブリッド選定フロー・難度 4 問・文章スロット一般化・失効検知・プロバイダ固有制約（Antigravity `runtimeMode`）を整合させる。
- [x] `config/.agents/skills/use-t3-code/SKILL.md` をハイブリッド方針・具体モデル表削除・`plan` / `implement` との役割分担・`models.md` リンクへ更新する。
  - frontmatter の description と本文の方針に矛盾が残らないようにする。

## Final Validation

- [x] 旧ファイル参照の不在確認: `rg --hidden -n "model-benchmarks" --glob '!docs/plans/**' --glob '!.git/**' .` → 0 件（exit code 1）。
- [x] 不変層からの具体モデル名排除確認: `rg -n "Terra|Sol|Astra|Luna|Haiku|Sonnet|Opus|Fable|Neon|Hydrogen|Carbon|Argon|gpt-6|claude-|gemini-4" config/.agents/skills/use-t3-code/SKILL.md config/.agents/skills/use-t3-code/references/delegation.md` → 0 件（exit code 1）。
- [x] `models.md` の ID・option 整合確認: 記載した `providerInstanceId`・`model`・option 名が `orchestrator_capabilities` の現行出力と一致することを差分レビューで確認する。
- [x] リンク・整合・書式確認: `SKILL.md`・`delegation.md`・`models.md` 間の相対リンク・アンカーがすべて実在すること、`plan/SKILL.md`・`implement/SKILL.md` との役割分担に矛盾がないこと、`git diff --check` が exit code 0 であることを確認する。
- [x] HOME 側の反映確認: `ls ~/.agents/skills/use-t3-code/references/` で `models.md` が参照でき `model-benchmarks.md` が消えていることを確認する（ディレクトリ単位の直接リンクのため即時反映）。

> 各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
