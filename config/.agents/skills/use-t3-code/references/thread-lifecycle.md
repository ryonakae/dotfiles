# スレッドの settle・archive

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

## 付随物を片付ける

settle・archive を頼まれたとき、またはプロジェクトの手順でスレッドを片付けるときは、このスレッドと子タスクが作ったものも片付ける。子は `t3_thread_list` の `includeSubagents: true` で `parentThreadId` がこのスレッドのもの、会話に記録した `taskId`・`t3_thread_launch` のスレッドで確かめる。

- **実行中の子タスク**: 不要なら `task_cancel` で止める。
- **子スレッド**: subagent の子スレッドは、親を settle すると T3 が一緒に settle する。`t3_thread_launch` で作ったスレッドは自動では片付かないので、このスレッドの作業のために作って終わったものを、親と同じ操作で settle・archive する。
- **ブランチ**: 子のブランチは `t3_worktree_list` に子の `threadId` を渡して調べる。PR の基点（PR がなければ既定ブランチ）に入ったものはローカルとリモートから消す。入っていないものは消さずに、名前と最後の commit をユーザーに示して確認する。
- **worktree**: 手動で消さない。T3 の `storageCleanup` に任せる。
- **Simulator など**: このスレッドと子が作った端末を消す。プロジェクトに手順やスクリプトがあればそれに従い、なければ作成時に記録した UDID で消す。名前だけで選ばず、記録にない端末には触れない。

消したものと、残したものとその理由を報告する。
