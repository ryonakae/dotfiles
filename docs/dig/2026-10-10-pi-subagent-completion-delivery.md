# dig log: Pi subagentの通知と作業完了

## 目的・前提・制約

- 対象セッション `01a1259a-262a-72e1-b81b-168bffd96be7` で、子の未完了終了と、親への完了通知の遅延を確認した。
- 7体中4体は担当範囲を残した最終回答で通常終了した。親の再開依頼後もhistoryは未完了で終了した。対象の終了記録は `stopReason: stop` / `rawStopReason: completed`。実行終了と依頼完遂は異なる。
- testflightとdataの通知は、実行完了からそれぞれ約21分36秒、16分47秒後、親の最終回答後に配信された。その後、親は反映済みとの応答を追加した。
- 導入版と開発用リポジトリ `/Users/ryo.nakae/Dev/private/pi-subagents` はコミット `be898c753e9eb32cf1315f63b1c1f5ef0cf6f782`。開発用リポジトリの作業ツリーは調査開始時に未変更。
- `src/nudge-queue.ts` と `src/index.ts` は、TUI/RPCの親がbusyの間は通知を拡張内に保留し、`agent_settled` で配信する。結果取得時には保留を取り消す。
- 個別・グループ通知、tool/RPC経由の結果取得、再開・停止・shutdown、print/JSONの既存契約を考慮する。
- dotfilesの既存変更は保持する。コミット・push・導入版の切替は、この調査では行わない。

## 決定事項

- 通知は実装、途中終了は指示と作業分割を中心に対処する。
  - 理由: 指示だけでは通知待ちを解決できず、本文による未完了判定の自動化は誤判定と無制限再開につながる。
  - 出典: 助手の提案に対するユーザーの「その方向で進めて」。
- 通知取消を維持しながら、親の最終回答まで待たず安全な境界で完了を知らせる。
  - 出典: 同上。
- 親は公式の結果取得ツールを使い、`completed` ではなく委譲した完了条件を照合する。大量の全文調査は意味のある小さな担当範囲に分ける。
  - 出典: 同上。
- 子は担当完了か具体的な継続不能理由がある場合に最終回答を返す。途中経過は最終回答にせず、追加指示が元依頼を置き換えない限り元作業を続ける。
  - 出典: 同上。

## 対象外

- 未完了回答の本文分類や自動再開ループ。
- モデルの一律な上位変更。
- 通知待ちのポーリング。
- `completed` を依頼完遂の保証に変更すること。

## 未決・保留

- 上流同期・Pi 1.1.0以上を前提とする修正は、境界配信の説明後の「ok 修正してみて」で実行承認された。開発依存のみ更新し、実機Pi本体の更新と導入拡張の切替は別途扱う。
- 上流確認結果（2026-10-10）: 最新masterは `fd8d81618d80ae83a3faf40cb87dae99cca33264`、共通祖先は `e955e29c51b7a6cce37e1108cd2d6c57a77e151c`。fork未取り込みは6コミット。v0.20.0（2026-10-09、`13106ab`）で最低対応・開発依存ともPi 1.1.0へ変更済み（`25eb4fa` / PR #384）。`pi --version` で現ホスト1.0.4を再確認。
  - [v0.20.0](https://github.com/tintinweb/pi-subagents/releases/tag/v0.20.0)、[Pi 1.1.0対応](https://github.com/tintinweb/pi-subagents/commit/25eb4fa)、[最新master](https://github.com/tintinweb/pi-subagents/commit/fd8d81618d80ae83a3faf40cb87dae99cca33264)。
  - 上流には `@handle` の会話・system prompt引継ぎ、子outputログの重複/system message混入、Workflowのisolated指定、FleetViewの修正がある。
  - 上流 `src/index.ts:443–522` は200msのhold後に `followUp` へ配信する既存方式。forkのbusy保留・グループ消費/再開世代の修正は上流にない。今回の境界配信案は未実装で、`src/prompts.ts` と `src/agent-runner.ts` に共通祖先からの上流差分はない。
  - 承認済み方針: 上流masterへ同期し、Pi 1.1.0以上の契約で再確認したうえで、必要なfork独自通知修正と指示修正だけを加える。Pi本体更新・導入版切替は別途計画・承認する。
  - 実装・検証の進捗は[計画](../plans/2026-10-10-pi-subagent-completion-delivery.md)に記録する。
- 承認済み配信設計: Pi 1.0.4の `turn_end` と補完用の `agent_before_settle` で、完了・未消費・未通知の結果を選び、既存 `event.entries` を保ったまま `custom_message` draftを追加する。通常終了で継続可能な場合だけ `continue: true` を返す。idle中の完了には既存の起動経路を残す。abort/errorでは通知による自動再起動を行わない。通知済みと結果取得済みは区別する。
  - 一次情報: インストール済みPiの `dist/core/extensions/types.d.ts:722–801`、`dist/core/agent-session.js:486–518` を確認。draftはモデルcontextとUI履歴の双方へ入る。Piへ投入したsteer/follow-upの個別取消APIはないため、投入前に拡張内で未消費を選別する。
  - 旧開発依存の `TurnEndEvent` は通知draftや継続制御を返す契約ではない。
  - 制約: 実行中のモデル出力や長時間tool自体は中断せず、境界まで待つ。他拡張のdraftを保持し、結果取得・resume世代・session切替と競合しないことをテストする。
- 指示の配置案: 親向けはdotfilesの `config/.pi/agent/agent-tool-description.md`、子向けは拡張の `src/prompts.ts` の共通部分。Explorer/Reviewerは `prompt_mode: replace` なので、親の指示変更だけでは届かない。この配置で実装する。
- テスト計画: 既存の `test/rpc-result-consumption.test.ts` と `test/nudge-queue.test.ts` に加え、busy中の配信・消費済み除外・resume世代・idle時の一度だけの起動を確認する。
- 会話で説明した変更順序と検証範囲への実行承認を受け、計画に記録して着手した。実機導入は未承認・未実施。
