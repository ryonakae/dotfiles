---
name: use-t3-code
description: >-
  T3 Code 環境でのサブエージェント委譲、worktree、iOS Simulator 操作の運用ガイド。
  内蔵のサブエージェント機能（Claude Code の Agent ツールなど）や T3 Code の delegate_task を使う前、
  委譲するかどうかの判断、委譲先の provider・モデル・思考レベル（effort / reasoningEffort）の選択、
  独立レビューの依頼先選び、子タスクの結果確認で使う。
  worktree を作成・移動・削除するとき（git worktree や内蔵の worktree 機能を使う前）にも使う。
  T3 Code の device_* ツールで iOS Simulator を開いて操作するとき、UI 動作検証や .ad テストを扱うときにも使う。
  スレッドを settle・unsettle・archive・unarchive するとき、スレッドの整理や片付けを頼まれたときにも使う。
---

# Use T3 Code

T3 Code が注入する指示に、この環境での判断基準と運用を補う。
`delegate_task`・`task_status`・`device_*`・`t3_thread_organize`・worktree 隔離などのツールの使い方と、内蔵機能と `delegate_task` のどちらを使うかは T3 の指示に従い、ここで再定義しない。

用途に応じて次を読む。

| 用途 | 読む資料 |
|---|---|
| サブエージェントへの委譲、独立レビューの依頼、子タスクの結果確認 | [references/delegation.md](references/delegation.md)。モデル × 思考レベルを比較するときは [references/model-benchmarks.md](references/model-benchmarks.md) も読む |
| iOS Simulator の操作、UI 動作検証、`.ad` テスト | [references/ios-simulator.md](references/ios-simulator.md) |

## worktree

worktree の作成・移動・削除は T3 Code で行い、`git worktree` や内蔵の worktree 機能（Claude Code の `EnterWorktree` など）を使わない。これらで作った worktree はスレッドに紐付かない。

- 作業中のスレッドを移す: `t3_worktree_handoff`
- 別スレッドや子タスクを worktree で動かす: `t3_thread_launch` の `workspaceStrategy`、`delegate_task` の `isolation`
- 削除: T3 Code がスレッドの削除・マージ時に片付ける

## スレッドの settle・archive

T3 Code main の文書と実装（2026-10-30 時点）に基づく。settle・unsettle・archive・unarchive はユーザーの依頼があるときだけ `t3_thread_organize` で行う。依頼された作業に unsettle・unarchive が必要なら、実行前にユーザーに確認する。

- **settle**: 終わった作業を Settled の棚へ移す。会話は続けられる。「片付けて」のように指定が曖昧なら settle を選ぶ。
- **archive**: サイドバーから外し、Settings → Archived へ移す。ユーザーが archive を指定したときだけ使う。

settle・archive のどちらでも PR の watch はすべて終わり、settled・archived のスレッドでは watch を始められない。watch を頼まれているスレッドは settle・archive しない。

settle の前に次の副作用を確認し、問題があれば先にユーザーに伝える。

- 未回答の async 質問は回答なしで破棄され、入力待ちのターミナルは閉じる。
- worktree のスレッドでは、プロジェクトの `runOnSettle` スクリプトが走り、プロジェクト設定によっては後の cleanup で worktree が削除される。
- pin と snooze が外れる。

archived のスレッドはメッセージを受け付けず、settle・unsettle・snooze・pin も拒否される。unarchive は archive の印を外すだけで、settle・pin の状態は archive 前のまま残る。

自動 settle はサーバーが T3 の設定に従って行う（一定期間の非活動、PR の merge・close）。pin しても自動 settle は止まらない。unsettle したスレッドは、新しい活動があるまで自動 settle されない。
