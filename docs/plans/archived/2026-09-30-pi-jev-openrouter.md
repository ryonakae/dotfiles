# JevのOpenRouter接続とPi標準認証 Implementation Plan

Status: アーカイブ済み（実装・検証・導入完了、後続変更でJev利用終了）。合成資格情報と偽HTTPによる実SDK検証・独立レビュー、両forkのcommit/pushと後続のmaster統合・reloadを記録済み。dotfilesへの反映は `fa45455`。その後 `a35be5a` でJev設定と個別の認証環境変数受け渡しを撤去した。

実OpenRouter接続・実資格情報・Pi 0.87.1以外の認証互換性は未検証のまま残す。実API試験はこの計画の対象外であり、今回も実行していない。以下のTypeSafe運用中・reload待ち・未commit表記は各段階の履歴で、現在の運用状態ではない。

後続の承認により両forkのmaster統合・導入更新・reloadまで完了。TypeSafeで運用中であり、実OpenRouter接続は引き続き未検証。以下は各段階の記録。最新の導入状態は[dig log](../../dig/2026-09-28-pi-jev-routing.md#導入完了時の記録)を参照。

Status: 実装・検証・独立レビューと両forkのcommit/push完了。後続の明示依頼により本番package参照を両forkのfeat/jev-routingへ切り替え、TypeSafeで両Jevを有効化済み。現在のセッションへの反映は/reload待ち。dotfilesのcommit/push/archiveと実API試験は未実施。

Preflight: staged変更なし。両forkは上記baseでclean・originと0/0。dotfilesは`ee9b494cbd73f9066d2fb3189a8f86f246d15d15`でoriginより1 commit ahead（既存のスキル文書変更）；未push commitと既存のClaude/Herdr/Zed/Pi設定・node_modulesを対象外として保持。今回編集するdotfilesの旧Jev差分は先行作業と一致し、開始時コピーを`/tmp/pi-openrouter-implementation/`へ保存した。

参照: [Dig LogのOpenRouter対応](../../dig/2026-09-28-pi-jev-routing.md#openrouter対応)。ユーザーはQ23で接続先の明示設定（A）を選び、その後「そのおすすめ案で」と、OpenRouterのPi標準認証再利用・TypeSafeの環境変数維持・独自キー保存機構を作らない方針に同意した。Dig Logの「提案（未承認）」はこの発言で承認済みとして扱い、実装時に記録を更新する。

開始時: 両forkの`feat/jev-routing`はclean。pi-subagents `e2ea8107d9c79fc1343ef8a893e845edf7551354`、pi-inline-skills `aabcfb9dfd9388f6cb2b556912b4c18cad1236ef`。dotfilesの既存変更は保持する。

## Requirements

- 両拡張に`jev.provider: "typesafe" | "openrouter"`を追加し、省略時は従来のTypeSafeとする。未知値は設定エラーとして扱い、別providerへ黙って切り替えない。
- TypeSafeは`TYPESAFE_API_KEY`を引き続き使う。OpenRouterはそのsessionの`ctx.modelRegistry.getApiKeyForProvider("openrouter")`によるPi標準認証を使い、保存済みキーも環境変数も利用できるようにする。独自の環境変数優先処理は追加しない。
- 認証の優先順位・キャッシュ・コマンド参照はPiに委ねる。`auth.json`の直接読書き、独自キー保存、TypeSafeのダミーmodel/provider登録、任意の認証コマンド実行機能は追加しない。
- providerの切替は明示設定だけ。別providerのキーによる代用、障害時のprovider間failover、新しいリトライは行わない。
- model/effort固定、Jev不採用時の親選定、Workflowの同一run継続、スキル手動ロードと標準read推薦、メインsession限定、入力の送信範囲、上限、閾値、明示offの無通信を維持する。
- 資格情報の実値・コマンド出力・認証例外のraw本文・HTTPエラー本文を診断やモデルcontextへ出さない。本物の資格情報ファイルを調査・変更しない。

## Implementation Decisions

### 接続とモデル

| provider | 接続先 | model省略時 | キー取得 |
|---|---|---|---|
| typesafe | `https://api.typesafe.ai/v1/systemone` | `jev-1.13.0` | `TYPESAFE_API_KEY` |
| openrouter | `https://openrouter.ai/api/v1/systemone` | `typesafe/jev-1.13` | Pi標準のOpenRouter認証 |

OpenRouterの[公式互換API](https://openrouter.ai/docs/guides/community/typesafe-sdk)は既存のstate/questionsとChoice/Noulのanswersを受け渡せる。Chat Completionsへの変換や新SDKは不要。providerのendpointは固定し、Piのmodel endpoint overrideをJevの送信先として流用しない。

`jev.model`を明示した場合はその値を使用し、provider変更時にも勝手に書き換えない。既存設定の`jev-1.13.0`をOpenRouterで利用できるとは確認できていないため、切替例ではproviderとmodelを一緒に変更するかmodelを省略する。既存のTypeSafe設定は変更なしで動く。

### 認証と非同期境界

- subagentsの小さなmodel registry interfaceを認証ストアに拡張せず、実際のAgent/Workflow contextから必要な認証解決だけをselectorへ渡す。親通知や子起動にキーを含めない。
- inline-skillsの起動時チェックと選定時処理にあるTypeSafeキー前提を除く。認証取得は選定対象batchの処理で行い、session開始時にOpenRouterの認証コマンドを不要に実行しない。手動本文挿入を認証の成否に依存させない。
- off、子sessionの自動スキル選定、固定済みAgent、候補なし/選定不要など、キーが不要な経路ではPi認証を呼ばない。既存の決定的な単一候補選択も通信なしで維持する。
- 新しいawait境界の前後で中断を確認する。inline-skillsはbatch/generation/sessionの有効性も確認し、古い依頼の資格情報取得完了を契機にHTTP送信・推薦しない。batch単位の判定再利用を維持し、provider retryで繰り返し認証・送信しない。
- 認証なし/取得失敗では、subagentsは既存の親選定要求、inline-skillsは自動推薦見送りと安全な診断に進む。Pi認証APIが使用不能でもTypeSafeや別キーへ代用しない。
- `timeoutMs`のHTTP処理・応答本文読取の制御は維持する。Pi標準の資格情報取得は別段階として扱う。Pi 0.87.1の`!command`は同期実行・最大10秒・process中cacheであり、拡張から厳密な5秒以内や即時中断は保証できない。これを隠して「認証を含め全体5秒」と案内しない。取得終了後に中断済みなら送信しない。

### 設定・文書・作業範囲

- forkのREADME冒頭と設定例、CHANGELOG、必要なsubagentsのguideを更新。OpenRouterキーは`/login openrouter`または環境変数で設定でき、保存credentialが環境変数より優先することを記載する。`auth.json`を暗号化保管と説明しない。
- dotfilesの両Jev設定には`provider: "typesafe"`を明示し、既存model・off・閾値を維持。`__safehouse_args.fish`へ`--env-pass=OPENROUTER_API_KEY`を追加し、環境変数利用者の起動経路を整える。Keychainやcredentialファイルのsandbox許可は広げない。
- 本番package参照、既存のキー保存方法、npm公開、実API試験は変更・実行しない。今回の計画ではcommit/pushは別途指示まで行わず、ローカル実装・検証・独立レビューまでを範囲とする。
- 共通パッケージや一般化したsecret管理基盤は追加しない。無関係な既知のJSONエラー診断等も修正しない。

## Tasks

- [x] **subagentsの接続/認証選択**: `/Users/ryo.nakae/Dev/private/pi-subagents`の`src/settings.ts`、`src/jev-selector.ts`、`src/index.ts`、`src/workflow/host.ts`と関連テスト・文書を変更。TypeSafe互換を保ち、Agent/Workflow双方からPi認証を利用できるようにする。
- [x] **inline-skillsの接続/認証選択**: `/Users/ryo.nakae/Dev/private/pi-inline-skills`の`src/config.ts`、`src/jev-client.ts`、`src/index.ts`と関連テスト・文書を変更。TypeSafe前提のチェックを除き、認証中の中断・batch切替を含めて既存の手動経路を保護する。
- [x] **dotfilesと利用案内**: `config/.pi/agent/subagents.json`、`config/.pi/agent/extensions/pi-inline-skills/config.json`、`config/.config/fish/functions/__safehouse_args.fish`へ上記の最小差分を適用する。キーの実値は扱わない。

## Final Validation

既存seamを使うTDDで、現在未対応のOpenRouter設定/通信経路をred→greenにする。subagentsのsettings/jev-selector/Agent/Workflowテスト、inlineのconfig/jev-client/automatic-context/session-lifecycleの適切な境界を使用する。

- [x] provider省略/各有効値/不正値、provider別model既定、明示modelの維持、ユーザースコープ限定を確認する。
- [x] fake HTTPでendpoint・Bearer・modelを確認し、TypeSafeがPiのOpenRouter認証を参照しないこと、OpenRouterがTypeSafe環境変数を流用しないことを確認する。
- [x] off/固定済み/選定不要/子スキルで認証取得・HTTPが0回、認証失敗時の既存fallback、認証待ち中のabort/session・batch切替で送信なしを確認する。秘密のsentinelを例外に含めても診断へ出ないことも検証する。
- [x] Pi 0.87.1のisolated SDKで合成OpenRouter資格情報と偽HTTPを使用し、Pi標準認証の取得、保存credential対環境変数の優先順位、Agent・Workflow・スキルの経路を確認する。ホストのauth.jsonや実キーを読み込まない。
- [x] subagentsは変更testを`npx vitest run <対象>`で確認し、最後に必須`npm run check`。inlineは`bun test`、`bun run format:check`、`bun run lint`、`bun run typecheck`。検証時だけNode 22.20.0を選択し、global pinは維持する。
- [x] fish構文を`fish --no-execute config/.config/fish/functions/__safehouse_args.fish`で確認。diffとJSONを確認し、両Jev off・従来provider/model・本番package参照・sandboxのファイル権限が維持されていることを確かめる。
- [x] 独立レビューでキーと送信先の対応、診断漏えい、非同期中断、親選定/手動スキルの回帰を確認する。修正後も重大指摘が残る、新しいhighが出る、設計変更が必要になる場合は修正を重ねず停止する。

## 検証記録

- subagents: TDD settings/selector/wiringでred→green。親のself-review後に不要な型castを除き、不正provider値のテストを追加。最終の変更6 filesは246 pass、必須`npm run check`はlint/typecheck成功・108 files / 2232 pass / 7 skip。ログ: `/tmp/pi-subagents-{red,green}-{settings,selector,wiring}.log`、`/tmp/pi-subagents-changed-tests.log`、`/tmp/pi-subagents-full-check.log`。
- inline-skills: TDD config/client/contextでred→green。親のself-reviewで`provider: null`がTypeSafeへ既定化されることを発見し、strict undefinedだけ既定化する修正を追加（nullのred→green確認済み）。最終107 pass / 0 fail / 330 assertions / 14 files、format・lint・typecheck成功。ログ: `/tmp/pi-inline-skills-tdd/`、`/tmp/pi-inline-skills-validation/`。既存の他のnullable設定は変更なし。
- 両forkの最終checkは`env -i`、Node22.20.0、一時HOME/TMPDIR/agent dirと合成キー、PI_E2E_LIVE=0で実行。global Node設定は不変。
- 実SDK 0.87.1 + fake HTTPは9ケースPASS: 認証優先順位、Agentの保存/env/runtimeキー、Workflowの保存/envキー、Agent+スキルの保存/envキー、両機能off。親handoff・同一Workflow継続と既存gateの非再実行・定義優先・標準read・子session抑止・off時HTTP 0回を確認。harness/log: `/tmp/pi-openrouter-implementation/{auth-sdk.ts,parent-sdk.ts,combined-sdk.ts,run-sdk.sh,sdk-matrix.log}`。null不正値の補強と型cast除去はこのSDK matrixの正常入力・生成JavaScriptの挙動を変えないため、結果を再利用する。
- dotfiles: fish構文成功、開始時コピーとの比較によりprovider明示とOpenRouter env-pass以外の設定・権限変更なし。本番package参照もbyte一致。確認script: `/tmp/pi-openrouter-implementation/check-dotfiles.mjs`。
- 全repoで`git diff --check`成功。forkの変更23 filesにuntracked生成物はなく、レビュー用diff/hashを`/tmp/pi-openrouter-implementation/review/`へ保存。commit/pushなし。
- 独立reviewer `923dc504-36b9-49b`（実装者とは別context）はblocking/high・decision required・medium/lowいずれも指摘なし。対象外の既存JSON.parse診断は今回の差分で悪化していない。修正cycleなし。
- レビュー後、23 filesのhash一致、dotfilesの差分限定、全repoのdiff check成功・staged差分なし・HEAD不変を再確認。既存の無関係なdotfiles変更と未push commitを保持した。
- 未検証: 実OpenRouter API/実資格情報での接続、Pi 0.87.1以外の実SDK認証互換性。本番の両Jevはoff、package参照も従来のまま。
- 後続の公開承認に基づき、両forkのレビュー済みhashとstage内容の一致・remote base不変を確認して各1 commitを作成。subagents `95119ca`、inline-skills `9e2b286`。双方の`origin/feat/jev-routing`へのpush成功、worktree clean・ahead/behind 0/0。doc-updaterは既に更新済みのため追加更新不要と判断。dotfilesの変更や既存未push commitは含めていない。

## 後続承認による本番設定切替

- ユーザーの「pi-inline-skills と pi-subagents も、fork 版に差し替えて。jevの設定もして」で本番切替を承認。両package参照を`git:github.com/ryonakae/<repo>@feat/jev-routing`に変更し、対象を限定した`pi update <source> --no-approve`でインストール。実体HEADはsubagents `95119ca`、inline-skills `9e2b286`。
- 両`jev.enabled`をtrueへ変更。provider:typesafe、model:jev-1.13.0、閾値・候補・送信上限・除外リストは維持。TypeSafe環境変数は存在だけ確認し、値は表示・保存していない。Node22.20.0はインストール時だけ使用し、global pinは維持。
- `agent-tool-description.md`の手動選定固定文と比較表を`{{modelSelectionGuide}}`へ置換。Jev有効時にauto guideを展開し、off時にはmanual guideを展開する既存機能を利用。委譲判断の前半はbyte一致で維持し、Agent/Workflowとも定義固定値優先を記載した。
- インストール先の実コードと実際のカスタム説明を使い、合成キー・fake HTTP・faux modelのisolated SDK検証PASS（Choice 1回、スキル推薦1回、標準read 1回、child判定false/true）。`pi list`、JSON差分比較、`git diff --check`も成功。ログ/harness: `/tmp/pi-jev-deploy/`。npmがinlineのインストールcacheに生成した未追跡package-lock.jsonだけは保持し、forkのtracked sourceに変更なし。
- この時点では既存セッションは再ロードしていない。実TypeSafe/APIモデル実行による疎通確認も行っていない。

各タスクは対応する検証が成功してから完了にする。軽微な差分と検証結果は該当箇所へ反映し、要件・対象外・公開契約の変更はユーザーへ確認する。最終確認では有効な結果を再利用し、計画と実際の変更を照合する。本件は本番切替が別承認の作業に属するため、commit/push・本番切替・archiveは追加指示まで行わない。
