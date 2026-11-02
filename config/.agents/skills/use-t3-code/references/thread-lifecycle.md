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
