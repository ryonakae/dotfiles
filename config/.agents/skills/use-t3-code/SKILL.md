---
name: use-t3-code
description: >-
  T3 Code 環境でのサブエージェント委譲、worktree、iOS Simulator 操作の運用ガイド。
  T3 Code で作業するときは、作業を始める前に読む。
  内蔵のサブエージェント機能（Claude Code の Agent ツールなど）や T3 Code の delegate_task を使う前、
  委譲するかどうかの判断、委譲先の provider・モデル・思考レベル（effort / reasoningEffort）の選択、
  独立レビューの依頼先選び、子タスクの結果確認で使う。
  T3 Code で文章作成・推敲・ドキュメント更新を行うときの Gemini 優先方針にも使う。
  worktree を作成・移動・削除するとき（git worktree や内蔵の worktree 機能を使う前）にも使う。
  T3 Code の device_* ツールで iOS Simulator を開いて操作するとき、UI 動作検証や .ad テストを扱うときにも使う。
  スレッドを settle・unsettle・archive・unarchive するとき、スレッドの整理や片付けを頼まれたときにも使う。
---

# Use T3 Code

T3 Code が注入する指示に、この環境での判断基準と運用を補う。
`delegate_task`・`task_status`・`device_*`・`t3_thread_organize`・worktree 隔離などのツールの使い方と、内蔵機能と `delegate_task` のどちらを使うかは T3 の指示に従い、ここで再定義しない。

## 委譲の方針

委譲できる作業は、指示を待たずにサブエージェントへ委譲する。T3 Code ではこの方針を、ハーネスやツールの説明にある「迷ったら起動しない」などの既定より優先する。少なくとも次の時点で、委譲するか判断する。

- 作業を始めるとき: 範囲を限定できる調査・探索、互いに依存しない作業
- Plan・設計案をユーザーへ出す前: 独立レビュー
- 実装・検証を終え、完了を報告する前: 差分の独立レビュー（数行の自明な変更は除く）
- 文章作成・推敲・ドキュメント更新をするとき

## 資料

用途に応じて次を読む。

| 用途 | 読む資料 |
|---|---|
| サブエージェントへの委譲、文章作成・ドキュメント更新、独立レビューの依頼、子タスクの結果確認 | [references/delegation.md](references/delegation.md)。モデル × 思考レベルを比較するときは [references/model-benchmarks.md](references/model-benchmarks.md) も読む |
| iOS Simulator の操作、UI 動作検証、`.ad` テスト | [references/ios-simulator.md](references/ios-simulator.md) |
| worktree の作成・移動・削除 | [references/worktree.md](references/worktree.md) |
| スレッドの settle・unsettle・archive・unarchive、整理・片付け | [references/thread-lifecycle.md](references/thread-lifecycle.md) |
