# Jev不採用時の親によるmodel/effort選定 Implementation Plan

Status: アーカイブ済み（実装・導入完了、後続変更でJev利用終了）。必須の回帰検証・実SDK検証・独立レビューが完了し、後続のmaster統合・reload・通常Agentの親選定と実子起動をdig logで確認した。dotfilesへの反映は `fa45455`、Jev設定の撤去は `a35be5a`。実Workflowの本番動作や選定による費用・精度改善まで確認したものではない。以下の未公開・未切替・未commit表記は当時の記録として残す。

後続の承認により本番導入・master統合・reloadまで完了。以下は各実装段階の記録。[dig logの導入完了記録](../../dig/2026-09-28-pi-jev-routing.md#導入完了時の記録)に、導入後の親選定フォールバックと実子起動の確認を記載した。

Status: ローカル実装・検証・独立レビュー完了。今回差分の指摘なし、correction cycleなし。その後、ユーザーが両フォークのcommit/pushとinline-skillsの公開リポジトリ作成を承認し、2026-09-29に完了。本番切替、npm公開、dotfilesのcommit/push、archiveは未実施。

開始時base: pi-subagents `ea5fb93a9ee9892be405c6a8f9b12687fbc7d090`。stagedなし、masterはorigin/masterと同一。先行実装のdirtyは既知の作業対象として保持。差分と開始時ファイルsnapshotは`/tmp/pi-parent-routing-M14YsQ/`。独立レビューはHEADとの差分全体ではなく、このsnapshot以後の今回差分を基本対象とする。dotfilesのClaude/Herdr/Zed/Pi設定等の無関係変更、出自未確認の`node_modules/`は変更しない。

参照: [dig log](../../dig/2026-09-28-pi-jev-routing.md)、[先行計画](2026-09-28-pi-jev-routing.md)。この計画は先行計画の「モデル選択失敗時の単純継承」と「Workflowの呼び出し指定優先」を置き換える。inline-skillsの実装・検証結果は変更しない。

## Requirements

- ユーザーが確認した優先順は、agent定義の固定値 → 未指定部分をJevが選定 → Jevが選べなければ実際の親エージェントが判断して明示指定 → 子を起動。model/effortの片方だけ固定の場合も、その固定値を変えない。
- 親判断とは、親のmodel/effortの継承ではない。別LLMへの代理選定や、親が毎回予備候補を先に計算する方式に置き換えない。
- 通常のAgentとWorkflow内の新規agentを対象にする。明示的な呼び出し指定も定義の空欄だけを埋める固定値として尊重する。通常の自動選定依頼では未指定にする。
- 低confidence・棄権・タイムアウト・API失敗・候補なし等では、未指定の値が親により確定するまで子を起動しない。中断は親選定依頼に変換せず、そのまま中止する。
- 定義のmodelが解決できない場合、黙って親modelへ置換しない。固定値の問題を明示し、起動しない。
- Jevを明示的にオフにした場合は旧Q13どおりAPIを呼ばず従来の手動指定/継承を維持する。ただし定義優先への統一はオン/オフ共通。既存セッションのresumeでは再選定しない。scheduler/nested/RPCへのJev適用拡大はしない。
- 両Jevの本番設定はoff、package参照・confidence 0.7・候補と比較指標は維持する。前の実験で作った用途説明の正式反映は今回に含めない。
- 既存の未コミット変更と無関係なファイルを保持する。stage/commit/push/公開/本番切替は行わない。Pi本体・内部API・表示patchは使わない。

## Implementation Decisions

以下の公開API追加と実行方式は、計画承認時に合意済み。

### 通常のAgent

Jev不採用時は、子を作成する前に`model_selection_required`を示すツール結果を返す。未指定項目、固定値、選定不能理由、選定ガイドの参照先を親へ伝える。親は元の委譲内容を維持し、未指定だったmodel/thinkingを指定して既存の`Agent`を呼び直す。初回に子は作らないので、再呼び出しは再開ではなく新規起動。値が揃った二回目はJevを再呼び出さない。

明示オフと、オンだがガイドが使えず自動選定不能な状態を混同しない。既存の`fallback`結果に含まれる無効化・固定済み・不採用を区別して、必要な場合だけ親へ返す。

### Workflow

Workflow全体を終了・再実行せず、同じ実行内の該当agentだけを選定待ちにする。成功済みjob/gateは再実行せず、独立して進行できるjobは続ける。現在のjournalは成功した連続prefixだけを再利用するため、`resumeFromRunId`で今回の選定待ちを解決しない。

- 親への通知はPi公開APIのcustom messageを`followUp`・`triggerTurn`で送り、元の親セッションに判断を戻す。別セッションを親の代理にしない。
- 既存の`SubagentWorkflow`へ、同一runの選定待ちを解決するモードを加える。提案する呼び出しは`{action:"route", runId, decisions:[{agentId, model?, effort?}]}`。通常のscript実行ではaction省略を維持する。実行中runを選定する操作と、終了済みrunのjournal再利用を混同しない。
- `runId + agentId`で待機対象を対応付ける。通知には対象タスク、固定値、未指定項目、理由を含める。通知は必要な情報に絞り、過大な本文・候補表を反復して親contextへ送らない。
- 親指定は通常の手動指定と同じmodel registry・enabledModels・対応effortの制約で検証する。Jev候補表を新しい利用許可リストにはしない。固定値に反する指定、不足、無効・古い・重複IDは起動せずエラーにする。batchは全件を検証してから受理する。
- 親が指定するまで待機し、勝手な時間切れ継承はしない。待機状態を表示し、既存のskip/stopで中止できるようにする。新しい待機時間設定は加えない。
- 選定待ちは子実行のconcurrency slotを占有しない。一方、選定をslot外へ移すだけで大量のJev要求が無制限に並ぶ変更もしない。現在の同時実行上限で選定開始を制限し、親待ちの間はpermitを返し、起動前に再取得する。
- 中断・session終了/切替で待機を無効化する。別sessionへ通知/選定結果を持ち越さない。pause中に親の回答が来てもpauseを無視して起動しない。親通知不能なら継承へ戻さず、そのagentを起動不能として報告する。
- 同一プロセス内の継続を保証範囲とし、crash/reload後の待機復元や任意の外部副作用のexactly-once保証は新設しない。liveなrunを`resumeFromRunId`で複製しない。

### 既存コードで確認した境界

- `src/invocation-config.ts:resolveAgentInvocationConfig`は定義優先。`src/workflow/host.ts:spawnAgent`は現在呼び出し指定優先で変更が必要。
- `src/index.ts`の通常AgentはJev後・manager起動前に戻れる。Workflowは同ファイルの`workflowTasks`とdetached実行・親へのfollow-up通知を利用できる。
- `src/workflow/runtime.ts`は現在semaphore取得後に`host.spawnAgent`を呼ぶため、その中で親を待つだけの実装にはしない。journal replay hitは新たな選定処理より前に返す。
- `src/workflow/journal.ts`は並行実行で後続jobが先に完了しても、先行に未完了があれば後続を再利用できない。今回の待機をrun終了に変換すると二重実行の危険がある。

## Tasks

- [x] **通常Agentの親選定要求と固定値保護**: `/Users/ryo.nakae/Dev/private/pi-subagents/src/index.ts`、`src/jev-selector.ts`、必要な既存model解決処理を変更。子を作らず親へ返し、親の再呼び出しで固定値を守って一度だけ起動する。Jev有効状態とガイド失敗の区別も扱う。
- [x] **Workflowの選定待ちと同一run継続**: `src/workflow/host.ts`、`runtime.ts`、`task.ts`、必要なprogress表示と`src/index.ts`の公開Toolを変更。定義優先、親への通知、route受理、slot管理、中断・pause・skip・session切替を一貫して扱う。用途が一つの汎用brokerや永続キューは作らない。
- [x] **説明と設定ガイドの整合**: dotfilesのauto-guideと先行計画の置換注記を更新済み。repoの公開契約との照合完了。`README.md`、`docs/workflows.md`、`CHANGELOG.md`、`src/workflow/tool-description.ts`、`examples/agent-tool-description.md`とdotfilesの`config/.pi/agent/model-selection-auto-guide.md`を新契約へ更新。旧計画の該当記述には本計画で置換されたことを示し、過去の検証結果を消さない。オン時は通常省略、不採用時に親が実際に判断するよう案内する。

## リモート保存

ユーザーの追加承認により、両フォークを`feat/jev-routing`へcommit/push。README冒頭にフォーク元・主な独自改修・ブランチの導入方法を追記。コードは検証済みの内容から変更していない。

- pi-subagents: `e2ea8107d9c79fc1343ef8a893e845edf7551354`。既定`master`は`ea5fb93`のまま。
- pi-inline-skills: `c0ab085a8ee0221ab4bccfd94a56914e392fa051`でLICENSE実体と出自を記録、`aabcfb9dfd9388f6cb2b556912b4c18cad1236ef`でJevと関連変更を記録。元の25コミットを保持し、`master`と機能ブランチを新規公開repo `ryonakae/pi-inline-skills`へpush。既定は機能ブランチ。
- 両repoはclean、upstreamとのahead/behindは0/0、`ls-remote`で各commitを確認。PR・npm公開・本番切替はしていない。dotfilesの変更はcommitしていない。

## 実装・検証記録

- repoの実装と対応ドキュメントを更新。今回のみの差分は`/tmp/pi-parent-routing-M14YsQ/implementation.diff`（23ファイル、764追加/94削除）。before/after snapshotは同ディレクトリ。ignoredの既存`.DS_Store`等は今回差分に含めない。
- 実装担当のTDD記録: 通常Agent、Workflow通知、定義優先、無効batch、session切替、待機表示でred→green。独立job/gate、pause/skip/abort、slot再取得、部分固定、scopeも検証。`npm run check`は108 files / 2213 passed / 7 skipped、lint・型検査成功。Node 22.20.0、一時agentDir、合成キー、PI_E2E_LIVE=0。既存のVite config警告以外の問題なし。
- 親による実Pi 0.87.1 SDK確認: `/tmp/pi-parent-routing-sdk.ts`をNode 22.20.0で実行し、`agent`・`workflow`の2ケースPASS。faux親/子・HTTP fakeを使用し、外部APIや本物の認証情報は使っていない。
  - 通常Agent: 最初はJev confidence不足→子0。親がmodel/thinking highを指定して再呼び出し→子1、Jev要求は計1回、親mediumを維持。証拠 `/var/folders/55/dc4z6w01287dbgs2kk_5c0mc0000gp/T/pi-parent-routing-sdk-wAhQkW/evidence.json`。
  - Workflow: 本物のcustom通知を親が受信→本物の`SubagentWorkflow action:route`を1回呼び出し→同runで研究子をhighで起動。待機中に別の定義lowの子とgateが完了し、両者とも再実行なし。定義lowはscriptのhighより優先、親medium維持、Jev要求は計1回。証拠 `.../pi-parent-routing-sdk-4VEXwE/evidence.json`。
  - ハーネス初回の2失敗は、TranscriptContextのsystem message形式と、session生成後のfaux runtimeキー設定不足が原因。`/tmp`ハーネスだけを修正して再検証し、repoコードは変更していない。
- dotfiles側はauto-guideと旧計画の置換注記を更新。新API名・引数はrepoのREADME/workflowsと照合済み。両Jev off・confidence 0.7を再確認。
- 独立レビュー完了（`d3b6b214-3e05-487`、read-only / Sol high）。今回差分にblocking/high・decision required・medium/lowの指摘なし。レビュー側で`npm run typecheck`、`npm run lint`（176 files）、対象5 files / 221 tests成功。全体checkとSDKは実装担当・親の結果を利用し、レビュー側では重複実行していない。先行計画の既知の残件まで再評価したものではない。
- 最終照合: `/tmp/pi-parent-routing-unchanged.mjs`でrepoのtracked/untracked対象234ファイルがレビューsnapshotから不変と確認。repo/dotfilesの`git diff --check`成功、stagedなし、両Jev off・confidence 0.7・本番package参照が従来どおりであることを確認。実API・実モデル実行・本番動作は今回未検証。

## Final Validation

TDDで先に現在の誤った継承・優先順位を再現し、変更対象のテストをred→greenで確認する。既存の`test/agent-model-display.test.ts`、`test/jev-selector.test.ts`、`test/workflow-effective-config.test.ts`、`test/workflow-runtime.test.ts`、`test/workflow-tool.test.ts`、`test/workflow-journal.test.ts`等の適切なseamを使い、必要な場合だけ専用テストを追加する。

- [x] 定義両固定/片方固定、呼び出しとの競合、無効な固定model、Jev採択/不採用/中断/明示offを確認。未確定時はspawn=0、親指定後はspawn=1・追加Jev=0。定義値と実効表示の一致も確認する。
- [x] Workflowで一つのjobを親待ちにしたまま独立jobとgateを完了させ、route後にそれらを再実行せず残りだけ進むことをカウンタで確認。親待ちによるslot枯渇とJev要求の無制限並列化を防ぐ。
- [x] 複数待機、重複/無効/batch不整合の回答、中断/skip/stop、pause中の回答、session切替を検証し、古い回答やabort競合から起動しないことを確認する。
- [x] 既存resumeとjournal replay hitで再選定・追加spawn・gate再実行が起きないことを確認。live runのjournal再開は拒否する。
- [x] `npx vitest run <変更したtestファイル...>`を対象repoで実行。最終に必須の`npm run check`を実行し、型・lint・全体回帰を確認する。検証時だけNode 22.20.0をPATH先頭へ置き、グローバル設定は変更しない。
- [x] 実Pi 0.87.1のisolated agentDirとfaux providerで、親への実custom message → 親による実Tool call → 同一Workflowの子起動を確認。通常Agentの二回の呼び出しも確認。Jevは偽HTTP応答を用い、APIキー・実モデル・本番設定を使わない。
- [x] 独立レビューで親/子セッションの取り違え、二重起動、slot解放と中断の競合、定義優先を確認する。修正で元の重大指摘が残る、新たなhighが出る、要件/APIの追加判断が必要になった場合は、修正を積み重ねずユーザーへ戻す。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。本件は既存の公開・切替承認待ち作業に属するため、commit/push・本番切替・計画アーカイブは別途承認まで行わない。
