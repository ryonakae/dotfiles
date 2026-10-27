---
name: use-t3-code
description: >-
  T3 Code 環境でのサブエージェント委譲と iOS Simulator 操作の運用ガイド。
  内蔵のサブエージェント機能（Claude Code の Agent ツールなど）や T3 Code の delegate_task を使う前、
  委譲するかどうかの判断、委譲先の provider・モデル・思考レベル（effort / reasoningEffort）の選択、
  独立レビューの依頼先選び、子タスクの結果確認で使う。
  T3 Code の device_* ツールで iOS Simulator を開いて操作するとき、UI 動作検証や .ad テストを扱うときにも使う。
---

# Use T3 Code

T3 Code が注入する指示に、この環境での判断基準と運用を補う。
`delegate_task`・`task_status`・`device_*`・worktree 隔離などのツールの使い方と、内蔵機能と `delegate_task` のどちらを使うかは T3 の指示に従い、ここで再定義しない。

用途に応じて次を読む。

| 用途 | 読む資料 |
|---|---|
| サブエージェントへの委譲、独立レビューの依頼、子タスクの結果確認 | [references/delegation.md](references/delegation.md)。モデル × 思考レベルを比較するときは [references/model-benchmarks.md](references/model-benchmarks.md) も読む |
| iOS Simulator の操作、UI 動作検証、`.ad` テスト | [references/ios-simulator.md](references/ios-simulator.md) |
