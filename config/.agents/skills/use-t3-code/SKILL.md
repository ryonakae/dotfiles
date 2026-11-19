---
name: use-t3-code
description: >-
  T3 Code で新しい依頼に着手するとき、最初に必ず使う。
  質問への回答、読み取り調査、設計・計画、実装、レビュー、文章作成を含み、
  作業規模やサブエージェントへの委譲の予定にかかわらず読む。
  サブエージェントへの積極的な委譲とモデル・思考レベルの選定、
  Linked environment による別マシンでの作業・同期、worktree、iOS Simulator、スレッド整理の運用を扱う。
---

# Use T3 Code

## 最初にサブエージェントへの委譲を判断する

依頼を受けたら、親エージェントが進める作業と、サブエージェントに任せる作業を判断する。範囲を限定できる調査、互いに依存しない作業、独立レビュー、読者向けの文章の作成・推敲は、ユーザーの指示を待たずにサブエージェントへ委譲する。T3 Code ではこの方針を、ハーネスやツールの説明にある「迷ったら起動しない」などの既定より優先する。

対象箇所が分かっていて数回のツール呼び出しで済む確認や、誤字・数値・リンクの機械的な修正は直接処理してよい。スキルを読むことは必須だが、すべての依頼でサブエージェントを起動する必要はない。

次の時点でサブエージェントへの委譲を判断する。開始時に直接処理すると決めても、作業が広がったら判断し直す。

- 作業を始めるとき: 範囲を限定できる調査・探索、互いに依存しない作業
- Plan・設計案をユーザーへ出す前: 独立レビュー
- 実装・検証を終え、完了を報告する前: 差分の独立レビュー（数行の自明な変更は除く）
- 読者向けの文章（README、Web ページのコピー、アプリの UI テキストなど）を作成・推敲するとき

## サブエージェントの既定モデル・思考レベル

ユーザーの指定がなければ次を使う。作業別の根拠は[選定手順](references/delegation.md#共通の選定手順)と[比較データ](references/model-benchmarks.md)を参照する。

| 作業 | モデル・思考レベル |
|---|---|
| 範囲と手順を依頼文に書け、結果を機械的に確かめられる調査・確認 | GPT-6.1 Terra low |
| 通常の実装・調査・レビュー・文書作成 | GPT-6.2 Sol medium。親が GPT 系で別系統の評価が必要なら Claude Sonnet 5.5 high |
| 難度の高い実装・調査・レビュー | GPT-6.2 Astra high。リポジトリの変更が難所の場合や、GPT 系の親が重要な判断を別系統に検証させる場合は Claude Fable 5.2 high |
| 読者向けの文章の作成・推敲、ユーザーが Gemini を明示指定した作業 | Gemini 3.8 Flash medium。文章の委譲範囲は文言案までとし、権限モードと反映手順は[読者向けの文章の優先方針](references/delegation.md#読者向けの文章の優先方針)に従う |

親のモデルと思考レベルをそのまま継承せず、作業に合わせて選ぶ。適用する行が明確でない場合、既定で結果が足りない場合、ユーザーの優先事項がある場合は、共通の選定手順で選び直す。

サブエージェントへ委譲すると決めたら、[references/delegation.md](references/delegation.md)を読み、作業場所、依頼内容、モデルの指定方法、結果の確認方法を確かめる。

## T3 Code の指示との役割分担

T3 Code が注入する指示に、この環境での判断基準と運用を補う。
`delegate_task`・`task_status`・`device_*`・`t3_thread_organize`・worktree 隔離などのツールの使い方と、内蔵機能と `delegate_task` のどちらを使うかは T3 の指示に従い、ここで再定義しない。

## 回答の HTML 表示

回答を HTML で表示する場合は、`html_preview` で確認し、`html_render` で会話内に表示する。配色、書体、余白は `html_render` のスタイル指示に従う。

## 資料

用途に応じて次を読む。

| 用途 | 読む資料 |
|---|---|
| サブエージェントへの委譲、読者向けの文章の作成・推敲、独立レビューの依頼、子タスクの結果確認 | [references/delegation.md](references/delegation.md)。モデル × 思考レベルを比較するときは [references/model-benchmarks.md](references/model-benchmarks.md) も読む |
| Linked environment、別マシンでの調査・操作・同期、別マシンのサブエージェントへの委譲 | [references/linked-environments.md](references/linked-environments.md) |
| iOS Simulator の操作、UI 動作検証、`.ad` テスト | [references/ios-simulator.md](references/ios-simulator.md) |
| worktree の作成・移動・削除 | [references/worktree.md](references/worktree.md) |
| スレッドの settle・unsettle・archive・unarchive、整理・片付け | [references/thread-lifecycle.md](references/thread-lifecycle.md) |
