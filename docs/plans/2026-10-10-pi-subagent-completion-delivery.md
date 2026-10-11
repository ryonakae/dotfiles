# Pi subagentの通知・完了指示の修正

## 承認・範囲

[設計記録](../dig/2026-10-10-pi-subagent-completion-delivery.md) と会話で説明した、上流同期、境界での通知、親・子向け指示の修正を実施する。ユーザーの「ok 修正してみて」を実行承認とする。実装時点ではコミット・push・実機更新を対象外とした。後続のユーザー承認により、両リポジトリのコミット・push、HomebrewでのPi更新、リモートコミット指定での拡張更新を追加した。

- 拡張の修正元: `/Users/ryo.nakae/Dev/private/pi-subagents`
- 開始HEAD: `be898c753e9eb32cf1315f63b1c1f5ef0cf6f782`
- 取り込む上流: `fd8d81618d80ae83a3faf40cb87dae99cca33264`
- dotfilesの修正対象: `config/.pi/agent/agent-tool-description.md`、`config/.pi/agent/settings.json` の拡張参照。既存のモデル追加は承認に従い部分stageで除外する。
- 既存のdotfiles変更は保持する。

## 実装と検証

1. 上流同期
   - [x] 変更前のlint・型チェック・通知関連テストを記録する。
   - [x] 上流6コミットをコミットせず取り込み、今回の競合だけ解消する。
   - [x] Pi 1.1.0の開発依存とlockを整合させる。実機Piは変更しない。
   - [x] 上流同期後の機械検証を行う。
2. 通知
   - [x] 既存Agent／結果取得／RPCとPi lifecycleイベントの接点で、busy中に次の境界で通知が届く失敗テストを書く。
   - [x] 完了・未消費・未通知の結果だけを `turn_end` / `agent_before_settle` で会話とUIに追加する。既存の他拡張のentriesを保持する。
   - [x] 同一ターンの結果取得、グループの一部/全部取得、再開前の古い通知、複数境界での重複、中断/エラー時の自動再起動、idle時の配信を検証する。
   - [x] 公開SDKを使ったスクリプト型テストで、モデル入力・履歴・継続の統合を確認する。実LLMの呼出しはしない。
3. 指示
   - [x] 親向け: 範囲分割、公式ツールでの結果取得、完了条件の照合を追加する。
   - [x] 子向け: append/replace共通の指示として、担当完了または具体的ブロッカー時のみ最終回答すること、追加指示が置換でなければ元作業を継続することを追加する。
   - [x] 既存プロンプト生成テストでappend/replaceへの適用を確認する。LLMの完遂率改善まで証明したとは扱わない。
4. 仕上げ
   - [x] README・変更履歴など、変更した契約の説明を整合させる。
   - [x] `npm run check` と変更した挙動に近い統合テスト、`git diff --check` を実行する。
   - [x] 独立レビューを行い、指摘があれば再現・修正する。
   - [x] 未コミットの上流取り込み、独自修正、検証、未適用範囲を分けて報告する。

## 対象外

- 未完了回答の自動分類や自動再開ループ。
- 親の実行中モデル出力や長時間toolへの割込み。
- `completed` の意味変更。
- 任意の新規依存追加、旧Piへの互換分岐追加。
- モデル・thinkingの選択方針や比較表の変更。

## 進捗・検証結果

- 上流同期を `e93fd1a`、通知・指示修正を `5f4be85487118ad1e4b992544acde3571cd32f6a` としてコミットし、`ryonakae/pi-subagents` のmasterへpushした。
- 同期前: lint/typecheck成功、通知関連2ファイル31テスト成功。同期後: lint/typecheck成功、通知関連とFleetViewの3ファイル86テスト成功。ログ: `/tmp/pi-subagents-upstream-sync.log`。
- npm installは成功。npmが脆弱性4件（moderate 3 / high 1）を報告した。依頼外の自動audit fixは行っていない。
- 通知実装: 境界で200ms holdとspawn debounceを確定し、custom_message draftを一度だけ配信する。結果取得済み除外、resume世代、group quorum、session切替、中断後のwake抑止を保持・検証した。局所回帰10ファイル231テスト成功。既存print関連4ファイルは16成功/4 skip（opt-in live LLM）。
- 実SDKの6ケースでprint/jsonの両境界、モデル入力と保存entry、他拡張のdraft保持、並列sibling完了後の一部/全件消費を確認した。境界handlerを外したcontrolは失敗し、復元後に成功。ログ: `/tmp/pi-subagents-boundary-tests.log`、`/tmp/pi-subagents-notification-regression.log`、`/tmp/pi-subagents-boundary-print.log`。通常型チェックと新SDKテストの型チェック、局所lint成功。
- 独立レビューの指摘を再現・修正した。tool実行中abort、最後の境界handler後の遅着、他拡張によるdraft除外/invalid entry、空group timer、stale idle sendを検証。保存entryで配信を確認し、拒否されたdraftの自動再提案は1回までとする。実SDK/print hostは14ケース、局所4ファイル70テスト成功。ログ: `/tmp/pi-subagents-boundary-review-fixes.log`。
- 既存通知テストの起動処理を実際のPiに合わせ、session_start/isIdleと終了処理を補完した。個人のglobal設定が混入する既存テストがあるため、最終全体checkは一時HOME/PI_CODING_AGENT_DIRと実NodeのPATHで実行した。`npm run check` はexit 0、lint（174 files）・型チェック成功、108 files / 2,203 tests passed / 7 skipped。Viteの将来のnative config loaderに関する既存警告は残る。ログ: `/tmp/pi-subagents-final-check.log`。
- 両リポジトリの差分チェックと競合未解消ファイルなしを確認した。実LLMの完遂率・対話TUI実画面は未検証。
- Safehouse内のbrew updateはCellar書き込み不可で停止した。追加承認を受けたHerdr通常ペインで `brew update && brew upgrade --yes pi-coding-agent` が成功し、Pi 1.1.0へ更新した。依存のNode 26.11.1とsimdjson 5.0.3も更新された。
- 設定を `git:github.com/ryonakae/pi-subagents@5f4be85487118ad1e4b992544acde3571cd32f6a` に固定し、`pi update <source> --no-approve` でGitHubから取得した。導入先HEADとremote masterの一致、導入先のclean状態、Pi 1.1.0、offline helpでの拡張フラグ登録を確認した。ローカル開発checkoutは参照しない。実行中セッションではなく、Piを再起動して使用する。
- 親向け指示を2項目追加した。子向けは共通blockを追加し、各モードで完了条件と追加指示の扱いを検査する4ケースを追加。各sliceで期待する不足により2ケース失敗（exit 1）を確認後、全33ケース成功（exit 0）、局所lint成功。ログ: `/tmp/pi-subagents-prompts-red.log`、`/tmp/pi-subagents-prompts-steering-red.log`、`/tmp/pi-subagents-prompts-steering-green.log`。
