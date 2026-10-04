# Pi Jev Routing and Inline Skills Implementation Plan

Status: アーカイブ済み（導入完了後、後続変更で利用終了）。実装・検証・独立レビューと両forkの公開・master統合・reloadの記録を確認し、dotfilesへの反映は `fa45455` で確認した。親選定へのフォールバックは後続の親選定計画、自動スキル本文挿入は[後続計画](2026-09-30-pi-inline-skills-auto-injection.md)で置換済み。`a35be5a` でdotfilesのJev設定・選定ガイドを撤去し、inline-skillsはupstream版へ戻した。

JSON.parse例外の断片漏えいに関するmedium指摘は未修正の記録を残す。候補用途説明の本番反映、未見タスクの選定品質・費用改善・長期精度も確認済みとはしない。以下の未完了表記とチェック状態は各実装段階の履歴であり、現行の再開タスクではない。

後続の承認により公開・本番切替・両Jevの有効化・master統合まで完了。以下は各実装段階の記録であり、当時のoff・未公開・未切替表記を現在の状態とみなさない。最新の導入結果と置換された仕様は[dig logの導入完了記録](../../dig/2026-09-28-pi-jev-routing.md#導入完了時の記録)を参照。

2026-09-29追記: モデル選択のフォールバックと定義優先順位は、承認済みの[親選定計画](2026-09-29-pi-parent-model-selection.md)で置換する。以下の過去の実装・検証記録は当時の結果として保持する。

状態: 初期実装・修正cycle 2まで実施済み。subagentsは修正・独立レビュー通過。inline-skillsは入力予約の流用問題により停止し、Q18〜Q21で再設計、Q22へのユーザーの「a」で全体設計と計画改訂を承認。改訂計画提示後のユーザーの「ok」で実装開始を承認。再設計のローカル実装・検証・独立レビュー完了。full reviewのhigh 1件は1回のcorrectionで解消し、scoped再レビューで新high/decision requiredなし。medium 1件は未修正として残す。ユーザー承認後に実Jev検証を実施。API疎通とスキル経路は成功。モデル選択は初回4例すべてfallbackだったが、候補の用途説明を一時追加した比較では既知4例すべて採用された。未見の費用重視タスクはなおfallbackで、用途説明は本番未反映・有用性の評価課題が残る。公開/本番切替が未実施のため全体計画は未完了・未archive。既存の修正履歴は以下に残すが、旧入力予約方式と自動本文挿入は本改訂で置換する。新規ローカルrepoは `/Users/ryo.nakae/Dev/private` 以下。両Jevはoff、commit・公開・push・本番切替は未実施。実API検証の結果は下記に記録。

開始時base: dotfiles `7d672bc0d99eb023a3837cb12d84f8ac3b9d3bba`、pi-subagents `ea5fb93a9ee9892be405c6a8f9b12687fbc7d090`。両方upstreamとの差分0/0、staged変更なし。subagentsはクリーン。dotfilesの既存変更はClaude/Herdr/Zed設定、PiのlastChangelogVersionのみで、保持する。検証用Nodeはインストール済み22.20.0をPATHで選択し、global pinは変更しない。

設計記録: [dig log](../../dig/2026-09-28-pi-jev-routing.md)。Markdown管理の初期合意に加え、再設計Q18〜Q22を反映する。Q22のA選択と、その後の実装承認を両文書へ記録済み。初期数値は変更せず、実測済みの推奨値とは扱わない。

## Requirements

### サブエージェント

- `ryonakae/pi-subagents` に、未指定のmodel / effortをJevで選ぶ機能を追加する。既存の`Agent`、`SubagentWorkflow`を置換しない。
- modelとeffortは組み合わせとして比較し、必要な品質を満たす範囲で時間・費用のバランスを取る。参考ベンチマークを個別タスクの成功率・品質保証として扱わない。
- 呼び出し指定・agent定義の固定値はJevで上書きしない。片方だけ固定されている場合は候補をその値で制約する。
- Jevには委譲タスク本文、agentの役割説明、候補と選定基準を送る。親会話や事前要約は送らない。タスク内のコード・機密情報は送信対象になり得る。
- エラー・タイムアウト・低信頼度時の従来継承は、[親選定計画](2026-09-29-pi-parent-model-selection.md)により「子を起動せず親が未指定項目を判断」に置換。ユーザーによる中断は親への選定依頼と区別し、起動を中止する。

### スキル

- `tifandotme/pi-extensions` の `packages/pi-inline-skills/` を履歴・MITライセンス付きで独立させ、`ryonakae/pi-inline-skills` として管理する。
- 手動`/skill名`の本文直接挿入、補完、既存custom message表示、`/loaded-skills`を維持する。Pi標準`/skill:名前`の展開は変更しない。
- Jevは補助スキルを選び、メインモデルへ標準`read`による読み込みを指示する。本文を直接挿入せず、モデル実行前のロードや指示への従属を強制・保証しない。明示指定があっても補助選択し、Jev失敗で手動ロードを失わせない。
- 通常の手動入力は応答前に本文を挿入・表示・保存する。実行中の追加入力は応答前に本文を渡し、表示・保存のみターン終了時に行う。未実行のreadや擬似tool call/resultを作らず、`@pi-kaush/pi-tool-call-markers`との共存を検証する。
- 自動選択はメインセッションだけ。サブエージェント内の既存の明示ロード・必要に応じた読み込みは維持する。
- 実際に消費されるuserメッセージを判定対象とし、テンプレート展開後の本文・他拡張が生成したuserメッセージも含める。その中の`/skill名`も手動指定扱いとする。入力元による旧除外は廃止し、テンプレートの再展開はしない。
- 今回の依頼と上限付きの直近user/assistant会話、候補スキル名・説明を送る。custom message・tool result・thinking・展開済みスキル本文・添付内容は送らない。現在入力にも履歴と同じ除外を適用し、明示指定・ロード済みスキル名を判断材料にする。
- skills catalogを残し、メインモデルによる補完的な読み込みを妨げない。
- 明示依頼専用スキルは名前の除外リストで自動選択から除外する。標準の`disable-model-invocation`も尊重する。明示ロードにはこの除外を適用しない。
- 同一branchの手動挿入・native展開・成功readによるロードを統合して重複を防ぐ。推薦だけではロード済みとしない。該当なし・低確度なら推薦しない。
- 自動選定は同一の実消費入力集合につき一度だけ。推薦は当該依頼の実行中のみ有効とし、成功readで該当候補を除き、新入力・中断・実行終了・branch/session変更で破棄する。指示は履歴へ永続化しない。

### 管理と安全性

- 両拡張に独立した`jev.enabled`を設ける。オフではJevへ通信せず、subagentsの既存解決とinlineの手動ロード・一覧・表示を維持する。inlineの判定対象とqueued表示時点は上記の合意済み変更を適用する。
- TypeSafe公式APIへ直接接続し、共通の`TYPESAFE_API_KEY`を使う。MCP adapterやGatewayを必須依存にしない。キーをGit・設定JSON・専用ログに保存しない。
- 選定方針、親への案内、候補・比較データはdotfilesで編集できる。ユーザー固有のモデル名・性能表・方針を拡張コードに固定しない。
- 他者の未コミット変更を保持する。特に`config/.pi/agent/settings.json`は既存変更があり、切替時は対象パッケージ項目だけを編集する。
- Nodeのグローバル設定変更、無関係なnpm脆弱性修正、他のJev拡張導入、compaction方式変更は対象外。
- Pi本体の変更・fork・内部API/表示へのpatchは行わず、公開APIを使う。入力へ相関用の識別子を埋め込まない。

## Confirmed Implementation Boundaries

- 作業用subagents: `/Users/ryo.nakae/Dev/private/pi-subagents`。Piが現在ロードするcheckoutは `~/.pi/agent/git/github.com/ryonakae/pi-subagents` であり、作業用repoを編集するだけでは本番へ反映されない。
- 先行実装時点では`src/invocation-config.ts:resolveAgentInvocationConfig`はagent定義 > 呼び出し指定、`src/workflow/host.ts:spawnAgent`は呼び出し指定 > agent定義。この差を維持する方針は[親選定計画](2026-09-29-pi-parent-model-selection.md)で撤回し、両方を定義優先に揃える。
- `src/index.ts:renderToolDescriptionTemplate` に既存プレースホルダー展開がある。ツール説明は登録時に生成される。
- `src/child-context.ts` のAsyncLocalStorageが `loader.reload()` と `createAgentSession()` を囲む。子判定をプロセス共通の一時環境変数で実装しない。
- inline-skills 1.0.6は`src/index.ts`で入力検出、`before_agent_start`でcustom message挿入、branch履歴からロード済み状態を復元する。
- Pi 0.87.1の`input`はskill/template展開前、`before_agent_start.prompt`は展開後。過去の標準`/skill:name`は展開本文付きuser messageとして残る。公開の`parseSkillBlock()`が`userMessage`を取り出せる。
- streaming中のsteer/follow-upは通常の`before_agent_start`経路を通らない。単一pending変数や単純なFIFOを追加するだけでは、スキル本文を対応する入力へ結び付けられない。
- upstreamのinline-skills packageにはテストスクリプトがない。monorepoには`bun run format:check`、`bun run lint`、`bun run typecheck`がある。package内の`LICENSE`は`../../LICENSE`へのsymlink。

## Implementation Decisions

### 設定と編集可能なガイド

正本を以下に分ける。

| dotfiles内のパス | 内容 |
|---|---|
| `config/.pi/agent/agent-tool-description.md` | 委譲判断・タスクの書き方・並列化・親の検証・失敗原因の切り分け。モデル選択部分を`{{modelSelectionGuide}}`へ置換 |
| `config/.pi/agent/model-selection-guide.md` | 共通の自然文の選定方針。Jevへの判定指示とJevオフ時の親向けガイドに使用 |
| `config/.pi/agent/model-selection-auto-guide.md` | Jevオン時の親向け案内。通常はmodel/thinkingを省略し、必要時だけ明示指定すること、フォールバック、再開時の扱い |
| `config/.pi/agent/subagents.json` | `jev`のオン・オフ、通信・判定設定、候補、構造化した比較データ |
| `config/.pi/agent/extensions/pi-inline-skills/config.json` | スキル側の`jev`設定、除外名、会話・自動追加上限 |

- `{{modelSelectionGuide}}`はオン時にauto-guide、オフ時に通常guideを読む。`{{modelCandidates}}`は候補・参考指標を設定から整形する。展開は既知のプレースホルダーに限定し、任意コード実行や再帰的テンプレート機構は追加しない。
- 共通guideには判定基準を置き、親だけの呼び出し手順とJevのJSON契約を混在させない。`model/thinking`とWorkflowの`model/effort`の引数名の違いは各ツールの説明で扱う。
- guideの表を自然文として解析して候補を復元しない。Jevには同じJSON候補データをChoice criteriaとして渡す。候補IDはコード側で生成する。
- 初期候補は現在の4モデルについて、既存DeepSWE表の20組み合わせを移す。スコア・誤差・時間・steps・参考USD、出典・日付・測定条件・価格補正・適用限界を保持する。明示指定のためだけに候補表を別途保守しない。
- 新しいJev設定とguideは初期版ではユーザースコープの正本を利用する。プロジェクト設定だけで外部送信を有効化したり、送信用guideを任意ファイルへ差し替えたりしない。既存の非Jev設定のproject overrideは維持する。
- JSON/Markdown編集の反映は`/reload`または新規セッションを境界とする。即時切替UIは追加しない。切替後のツール説明と実際の解決方式を一致させる。既に起動した子やロード済みスキルは巻き戻さない。
- guide欠落・不正設定では黙って別の選定方針を適用しない。既存継承へ戻す先行実装は[親選定計画](2026-09-29-pi-parent-model-selection.md)で見直し、明示オフとオンなのに選定不能な状態を区別する。Jev未設定の通常利用者が新しいguideファイルを必須にされないようにする。

### 初期設定案（計画承認対象）

| 項目 | 初期値・扱い |
|---|---|
| パッケージ既定 | `jev.enabled: false`。利用環境も別途承認まで両方offを維持 |
| Jevモデル | `jev-1.13.0`。バージョン変更は設定編集で行う |
| 接続先 | `https://api.typesafe.ai/v1/systemone`。初期版では任意endpoint設定を追加しない |
| 待ち時間 | 1判定全体で5秒、自動リトライなし。呼び出し元のabortも伝播 |
| モデル選択 | Choiceの`confidence >= 0.7`。初期仮説であり精度保証ではない |
| スキル選択 | 候補ごとのNoulを1リクエストにまとめ、`noul >= 0.85`の上位から最大3件。NoulにはconfidenceがないためChoiceと同じ閾値・名称を流用しない |
| スキル会話 | 今回の入力を含む最大6メッセージ、合計12,000文字。新しい発言を優先し、直前assistantを可能な限り保持。省略の有無を診断表示 |
| リクエスト上限 | UTF-8で64 KiB。超過時は候補やタスクを黙って削らず、警告してその判定を見送る。これはAPIトークン上限を保証する値ではない |
| 診断 | 有効状態、候補/スキル名、confidenceまたはnoul、遅延、フォールバック理由、切り詰め・上限適用の有無。task/会話/キー/APIエラー本文を専用ログに記録しない |

閾値・上限は設定で調整できるようにする。日本語の代表例で評価し、都合のよい例に合わせて合格条件を後から変更しない。

### subagentsの選択経路

- 最初の適用先はメインの`Agent`と`SubagentWorkflow`からの新規起動。再開は変更しない。nested delegation、scheduler、cross-extension RPCの既存のモデル解決は今回自動変更しない。
- 共通の小さなselectorを両入口から呼ぶ。agent定義/呼び出しの優先順位は入口で解決し、親からの継承を確定する前に未指定項目を渡す。manager全体へ無差別に挿入しない。
- 候補を`enabledModels`、利用可能なモデル、`getSupportedThinkingLevels()`で検証する。候補内のモデルは完全なprovider/model IDとし、曖昧名を選択結果から解決しない。明示指定の従来の曖昧名対応は変更しない。
- 両項目が固定なら通信しない。制約後の候補が0件なら警告付きフォールバック、1件なら決定的に補完する。2件以上は候補IDのChoiceに棄権選択肢を加える。APIの255選択肢上限を超える設定は拒否し、黙って切り捨てない。
- 返答の型、ID、確率の範囲、confidenceを検証し、未指定項目だけに反映する。親のmodelやthinkingを変更しない。
- 設定取得とツール説明、`src/workflow/tool-description.ts`の省略時説明、実際の選択を一致させる。実効model/effortは既存のinvocation記録・表示へ反映する。

### inline-skillsの入力・手動挿入

- `input`から後続イベントへの本文予約と、queueの先読みから入力を推測する処理を撤去する。FIFO、文字列不一致時の先頭fallback、無条件の全消去で関連付け問題を隠さない。
- 通常手動入力は`before_agent_start.prompt`から同期的に解決し、本文をそのイベントのcustom message戻り値に含める。認証/model preflight前に本文の保留予約を作らない。
- queued入力は`context`と現在branchの`buildSessionProjection()`を使い、実消費済みuser entryを扱う。all-at-onceでは最新1件だけでなく、当該要求のuser集合を対象にする。provider変換後はcustomもuser roleになり得るため、変換前の元user entryで識別する。
- queued手動本文は当該provider要求のcontextへ追加し、同じ内容を`pi.sendMessage(..., { triggerTurn: false })`で保存・表示する。Piがターン終了時に保存するまで、要求内の本文追加と保存予約の重複防止を分ける。実消費済み`sourceEntry.id`集合を使い、retryでcontextが再実行されても本文は要求へ渡し、保存・表示は一度だけにする。
- provider error/abortでも、既に当該要求へ渡した本文はそのターンの履歴として保存される。これは次入力への予約流用とは区別する。ロード状態の正本はactive branchの履歴。ファイルを読んだだけ・推薦しただけではロード済みとしない。
- native skill本文内の`/skill名`を新しい手動指定として走査しない。Piが展開した依頼部分だけを判定し、標準展開や添付を変更しない。展開無効、仮想template、slash先頭templateにも再展開を加えない。

### inline-skillsの自動選定・送信・寿命

- `context`で実消費済み入力集合の依頼部分と直近会話を取り出し、手動指定・既ロードを除いた候補をJevへ渡す。同じ現在入力を履歴と末尾へ二重に追加しない。候補なし・Jevオフ・子/識別不能セッション・キーなしでは通信しない。
- 現在入力・履歴の両方から全skill blockを除く。最初の`parseSkillBlock()`だけで済ませず、連続blockを含めて除外し、壊れた/閉じていないblockを含む文字列は送信しない。custom/toolResult/thinking/添付を除外する。「任意の文章内に引用された秘密」まで識別できるとは主張しない。
- 除外名は`commit-push`、`implement`、`doc-updater`、`ask-codex`、`herdr`、`plan`。`disable-model-invocation`を標準frontmatter解釈で尊重し、明示ロードには適用しない。存在しない除外名はエラーにしない。
- Jevの結果はスキル名と実在するSKILL.mdのパスを使ったread指示としてprovider contextにのみ追加する。拡張が自動候補本文を直接挿入したり、read済みの履歴を捏造したりしない。モデルが読まない場合の強制実行や追加のJev再試行はしない。
- 一つの実消費入力集合に対する判定結果（失敗/該当なしを含む）はprovider retryでも再利用する。読み込み指示とJev判定済み状態を区別し、成功read後に指示を除いても同じ依頼を再選定しない。新しい依頼への切替・中断・実行終了・branch/session変更で古い推薦を破棄する。
- 非同期Jev完了後にもabort、session generation、実消費入力集合の有効性を確認する。待機中に無効化された結果は適用しない。失敗時は推薦のみ省き、手動処理を維持する。ユーザー中断をfallback続行に変えない。
- 手動custom message、native展開、成功readを既存のbranchロード管理へ統合する。失敗readをロード済みとせず、read追跡・symlink・compaction復元の既存契約を保つ。推薦状態と永続ロード状態を混在させない。

### 再設計の実証と限界

- `/tmp/pi-manual-context-proof.test.ts`: 5 pass / 23 assertions。通常入力の即時表示、queued本文の応答前提供と遅延保存、preflight失敗、steer/follow-upのqueue clearを確認。
- `/tmp/pi-manual-context-extended-proof.test.ts`: 7 pass / 34 assertions。複数user、retry、provider/tool error、abort、branch、新規AgentSessionを確認。実runtime replacementによるnewSessionは未検証。
- `/tmp/pi-jev-conversation-boundary-proof.ts`: 現会話helperを展開後入力へ流用するとcurrent/2番目のskill本文が漏れる反例を確認。実本文・外部通信は使っていない。
- `/tmp/pi-jev-native-skill-display.ts`: tool-call-markers 0.3.8が有効なコンポーネントで、標準単一skillの折りたたみ/展開を30/80列で確認。実TUI全体・手動custom renderer・grouping・履歴再表示の合格ではない。
- これらは設計用の簡略ハーネスであり、実拡張の完成を示さない。必要な振る舞いをrepoの実装をロードする回帰テストへ移し、固定本文や試作ロジックをテスト内へ複製して実装の代わりに検証しない。

### メイン/子の識別と通信実装

- subagentsの既存AsyncLocalStorageを使い、読み取り専用の小さなcross-extension accessorを公開する。既存の`Symbol.for` registryの慣例に合わせ、inline-skillsは拡張初期化中に子コンテキストをcaptureする。async scope外へ抜けた入力イベントで都度推測しない。
- 子を識別できないバージョン組み合わせではこの統合の自動選択を有効化しない。互換性不足を通知し、明示ロードを残す。両forkの組合せを検証してからオンにする。
- HTTPはNode標準のfetch/AbortControllerで実装する。TypeSafe専用の第三の共有パッケージやMCP経由の通信層は作らない。各repo内に用途に必要な小さなクライアントとレスポンス検証を置く。
- APIキーはAuthorizationヘッダーだけに設定し、redirectを追わない。401/429/5xx/不正JSONなどを分類して表示するが、サーバーが返す未加工の本文は表示しない。abortはAPI失敗とは区別する。

## Tasks

- [x] **subagentsのJev設定・selector・編集可能な説明**: `/Users/ryo.nakae/Dev/private/pi-subagents` の `src/settings.ts`、`src/index.ts`、`src/workflow/host.ts`、`src/workflow/tool-description.ts` と、Jev選択/guide読み込みの小さな専用モジュールを変更する。
  - 進捗: 実装・一次検証・修正cycle 1の検証済み。cycle 1では中断保証が未解消で停止したが、承認済みcycle 2で修正・再レビュー通過。`src/jev-selector.ts`、`src/model-selection-guide.ts`追加、既存設定/Agent/Workflow/説明へ統合。focused 167 pass、mutation 3件の失敗を確認。空の一時`PI_CODING_AGENT_DIR`で`npm run check`: 2179 pass / 7 skip、`npm run test:e2e`: 68 pass / live 7 skip、`npm run build`成功。初回checkは24 fail（実global設定の混入に加え、guide期待値の更新漏れを含む）。期待値を修正し、hermetic条件で再検証した。
  - 初回レビューでhigh 2件を採用: 応答本文受信中のcaller abortがfallbackへ落ちる経路、enabledModels設定あり・一致なしが無制約になる経路。回帰テスト付き修正済み。cycle 1: focused 37 pass、check 2188 pass / 7 skip、e2e 68 pass / 7 skip、build・diff check成功（Node22.20、空の一時PI_CODING_AGENT_DIR、実キーなし）。
  - 再レビュー: 空scopeは解消。本文受信中の中断誤分類は解消したが、selector Promise解決後・caller継続前のabortでbackground spawnへ進める（`src/index.ts:1889`、spawn `:2140`）。callerのpost-await確認とAgent/Workflow統合回帰が不足。同じ中断invariantの未解消なので追加修正前に承認を求める。
  - cycle 2: `src/index.ts` / `src/workflow/host.ts`のselector await直後にcaller abort確認を追加。`src/settings.ts`は不正global Jev設定を生値非公開の警告で無効化。対応3テストファイルを更新。Red 3 fail→focused 115 pass、guard除去/警告への生値混入mutationを検出。Node22.20・空agentDirでcheck 2192 pass / 7 skip、e2e 68 pass / 7 skip、build/diff check成功。correctionは`/tmp/pi-subagents-jev-correction-cycle-20260928-175114/correction-only.diff`、同dirにログ。
  - cycle 2独立レビュー: 2件とも解消、新high/decision required/mediumなし。レビュアーもfocused 5 passを確認。commitは禁止継続のため未実施。
  - 既存`invocation-config`の優先順位とmodel scopeを維持し、設定の読み込み・保存で未知のJev状態が失われないよう境界を確認する。ユーザースコープの明示設定だけを送信許可とする。
  - `test/invocation-config.test.ts`、`test/settings.test.ts`、`test/tool-description-mode.test.ts`、`test/workflow-effective-config.test.ts`の既存ハーネスを使い、必要なselectorテストを追加する。TDDスキルで変更する。
  - README、`docs/workflows.md`、`CHANGELOG.md`のUnreleasedへ設定・省略時挙動・送信範囲・再読込条件を反映する。既存の無関係な仕様説明は変更しない。

- [x] **子コンテキストの安全な共有**: `src/child-context.ts`と拡張初期化/registry境界を変更し、読み取り専用の識別契約を用意する。
  - 進捗: version 1の`Symbol.for("pi-subagents:child-context")` accessorを実装。親の`/tmp/pi-jev-integration-check.ts`で実際の両forkをimportし、main/child並列で相互汚染がないことを確認済み。独立レビューで当該契約の問題なし。実Pi SDK統合でもmain=false / child=trueを確認。
  - `test/child-context.test.ts`にmain/child同時初期化、非同期継続、複数ロード時のidentity、mention用cloneの子扱いを追加する。
  - 初期化順・未対応バージョン時の動作を文書化する。環境変数による一時的なグローバルフラグや、別packageから内部ファイルを直接importする依存を作らない。

- [x] **inline-skills独立repoと手動挿入・自動read指示**: `/Users/ryo.nakae/Dev/private/pi-inline-skills` に対象packageを全履歴の作業用cloneから切り出す。元repoや既存subagentsの履歴を変更しない。
  - 進捗: upstream `d753b5c6e7a32534c8ff84cb1059d98cb2731f28`から切出し、baseline `689b311ff6cb093acdf7c6d3dac5ffa720e0904a`、25 commit保持。実装は未commitでremoteなし。MIT実本文・出自記録を保持。`bun test`:31 pass、format/lint/typecheck、pack dry-run（12ファイル）、diff check成功。queued入力は公開turn_end境界を用い、faux providerで基本的な消費前注入/連続入力/abortを検証。
  - 初回レビューでhigh 3件を採用: follow-upの予約が先行steerを妨げる、Jev待機中の終了/branch変更/abortを再確認しない、標準disable-model-invocationのYAML解釈が不十分。修正cycle 1でqueue別予約・消費時dedup、世代/abort/idle再確認、公開parseFrontmatter利用へ修正。Bun 37 pass、format/lint/typecheck、pack dry-run（12ファイル）・diff check成功。世代確認削除とdedup削除のmutationで回帰テストの失敗を確認。
  - 再レビュー: 旧3指摘の直接経路は解消。ただし新highとして、通常入力のpreflight失敗（モデル未選択/認証失敗等）で保留予約が残り、次の展開済み入力で一致しない場合に先頭予約へfallbackするため別入力にスキルを流用する（`src/index.ts:812`）。実入力との関連付け/失敗後の無効化が不足。追加修正前に承認を求める。公開APIで安全に対応できない場合はPlanに従い停止・相談する。
  - cycle 2: 認証preflight失敗→`/skill:beta next`および`/template next`で、失敗した`/alpha`本文の混入を実Pi 0.87.1/faux providerで再現（Red 2 fail、Green未達）。失敗入力はinputだけが発火。公開InputEventとBeforeAgentStartEventに共通入力IDがなく、preflight失敗の拡張通知もなく、idle時ctx.signalも未定義。古い予約と同時進行中予約を現在の方式で確実に区別できないため、コード変更前に停止。展開文字列推測/FIFO/全消去を修正済み扱いにしない。
  - cycle 2のsnapshot・再現テスト・red.logは`/tmp/pi-inline-cycle2.8MJt6D/`。correction.diffは空（repo変更なし）。既存Bun 37 pass、format/lint/typecheck/pack dry-run12ファイル/diff checkは再通過したが、新しい受入テスト2件の失敗を相殺しない。モデル未選択の個別再現と新方式は未検証。
  - package名を`@ryonakae/pi-inline-skills`へ変更し、配布入口は既存の`src/index.ts`を維持する。MIT本文を実ファイルで残し、元作者・upstream URL・基点commitと更新取り込み手順を記録する。README/assetsのリンクを修正する。
  - monorepo rootにしかない必要なdev dependencies、TypeScript/lint/format設定を対象packageに必要な範囲だけ移す。Piパッケージはpeerとして宣言し、検証用dev依存を用意する。
  - 再設計着手時baseは`689b311ff6cb093acdf7c6d3dac5ffa720e0904a`、stagedなし、remoteなし。既存差分は同作業の初期実装・cycle 1であることを確認して継続。新しい実装コード/テスト/docsをworker、独立SDK/TUIハーネスを親が担当し、編集対象を分離する。
  - 初期の切出し・設定・client・catalog・renderer・テスト基盤は再利用する。以下の再設計をTDDで実装し、旧予約の内部構造だけを期待するテストは新しい公開動作のテストへ置き換える。
  - **手動挿入経路**: `src/index.ts`、`src/loaded-skills.ts`、`src/read-tracking.ts`と`test/queued-input.test.ts`、`test/queued-state.test.ts`、`test/loaded-skills.test.ts`、`test/read-tracking.test.ts`。通常/queued経路を上記の実消費境界へ置換し、既存custom renderer・補完・一覧を再利用する。失敗入力の再現2件を先にrepo内へ移してRedを確認し、実拡張でGreenにする。
  - **Jev指示と送信境界**: `src/index.ts`、`src/conversation.ts`、`src/jev-client.ts`と既存conversation/clientテスト。自動本文挿入をread指示へ変え、実消費batchごとの一度だけの選定、推薦寿命、中断後guard、全skill blockの除去を検証する。小さな専用モジュールへの分離は状態と通信・履歴の関心分離に必要な範囲に留める。
  - **互換性と運用説明**: `README.md`、`CHANGELOG.md`へ手動/自動/nativeの違い、queued表示遅延、他拡張由来の送信、推薦はロード保証ではないこと、初期offを反映する。dotfilesの設定値・ガイド・本番参照をこの再設計だけで変更しない。
  - 再設計実装結果（独立レビュー前）: `src/input-batch.ts`を追加し、index/conversation/loaded-skills/jev-clientと回帰テスト・README/CHANGELOGを更新。Node22.20・隔離agentDirでBun 80 pass / 266 assertions、format/lint/typecheck、pack dry-run 13ファイル、diff check成功。preflight/queued保存時点/本文除去/read指示/abort分類/native複数block/idle再選定/推薦順序/slash先頭template/終了後continuationでRed→Greenを確認。実runtimeのnewSession/fork/switch、reload、合成summaryによるcompactionも検証済み。
  - 再設計full review（reviewer `ec55aa8b-e514-470`）: high 1件を採用。conversationは上限適用済みだが、別のcurrentInputフィールドがbatch全文を送るため、13,000文字入力や上限外のqueued入力が外部送信される。現在入力も同じbounded projectionに揃え、全payloadから省略部分が除外されるfetch捕捉テストを追加する。新規設計ではなく、既存送信上限の修正として1 cycle実施。
  - correction結果: `src/index.ts`、`src/conversation.ts`、`test/automatic-context.test.ts`の3ファイルのみ変更。Red 2 fail→Green 2 pass、全体82 pass / 276 assertions、format/lint/typecheck/diff check成功。snapshot・限定diff・ログは`/tmp/pi-inline-bounded-correction.0ZdQBk/`。親も限定diffを確認し、影響するSDKのskillのみ/両onを再実行して成功。UI/配布manifest/非変更のsubagents検証は有効な先行結果を再利用。
  - scoped再レビュー: 同reviewerがhigh解消、新high/decision requiredなしと確認。Node22.20・空agentDirで追加2テスト/10 assertionsも独立に成功。中断した旧予約方式のfindingは、新設計の実拡張回帰で再確認済み。commit禁止のためレビュー対象はbaseからのworking treeで、commitは作成していない。
  - 同レビューのmedium 1件は報告のみ: `src/config.ts`のJSON.parse例外を通知すると不正JSONの断片が含まれ得る。型検証エラーだけでなく構文エラーの固定カテゴリ化が望ましいが、今回のhigh修正には含めない。
  - packageの既存`test`、`format:check`、`lint`、`typecheck`を使う。テスト基盤の全面再設計は行わない。

- [ ] **dotfilesの方針・設定・認証受け渡し**: 上記のMarkdown 2ファイル、既存tool description、subagents設定、inline-skills専用設定を追加/変更する。
  - 進捗: Markdown 2ファイル、Jevオフの両設定、共通wrapperのenv-passを追加。新規3ファイルのsymlinkを既存配布方式で作成済み。現行tool descriptionの置換は新コード検証/切替時まで保留し、古い拡張へ未知のplaceholderを渡さない。
  - 検証: `/tmp/pi-jev-dotfiles-check.mjs`（Node22.20）で元のHEAD内比較表20行とJSONの全数値・model/effort一致、許可モデル、ペア重複なし、出典日付、除外名、Jevオフを確認。`fish -n config/.config/fish/functions/__safehouse_args.fish`、`git diff --check`成功。
  - 表の移動は元データと差分照合する。元の自然文の委譲判断・検証ルールを落とさず、モデル選定の正本だけ分離する。
  - `config/.config/fish/functions/__safehouse_args.fish`へ`--env-pass=TYPESAFE_API_KEY`を追加する。実キーの取得/入力はユーザー側で行い、既存のsecretファイルを読まない。denyルールや`--add-dirs`/`--enable`は変更しない。Hermes用wrapperへのキー受け渡しは追加しない。
  - 既存symlink配布手順で新規ファイルを展開し、直接`~/.pi`側の正本を編集しない。
  - 既存MCP adapterも同環境変数を認識することを説明する。通常検索ではJevを呼ばず、意味検索は明示操作であることを確認する。他拡張のJev設定を無断で変更しない。

- [ ] **組合せ検証と段階的置換**: まず独立した検証用Pi設定で両forkをローカルパスからロードし、オフ→モデル選択のみ→スキル選択のみ→両方オンを確認する。
  - 進捗: 親の`/tmp/pi-jev-integration-check.ts`でdotfiles設定を各forkの実parserへ渡し、on/offガイドと候補/出典維持、仮の新tool descriptionのplaceholder展開、実cross-package accessorを確認。API通信なし。さらに`/tmp/pi-jev-sdk-integration.ts`でPi 0.87.1 SDKへ両forkを実ロードし、独立したagentDirとfaux providerで新規Agentを起動。全4通り（両off/modelのみ/skillのみ/両on）が成功し、Choice/Noul各0または1回、child thinkingのmedium継承/low選択、main/child識別、skill本文が送信payloadへ含まれないことを確認。HTTPは全て偽応答、外部通信なし。ハーネス初期のtools指定、runtime key設定時点、Choice偽応答の不足はハーネス側のみ修正した。queued境界やpreflight失敗を覆う統合成功とは扱わない。
  - cycle 2後、親が同じSDK統合ハーネスの全4通りを再実行して成功。これは旧実装の通常経路の記録であり、再設計の合格とは扱わない。ハーネスをread指示方式へ更新し、偽mainモデルから実際の標準readを呼ぶ組合せ検証を行う。
  - 再設計後、親の更新済み`/tmp/pi-jev-sdk-integration.ts`で4組合せすべて成功。自動選択直後は本文なし、mainの標準read成功後のみ本文あり、子には本文なし、Choice/Noul各0または1回、子thinkingのmedium継承/low選択、main/child識別を確認。全通信は偽HTTP/provider。
  - 親の`/tmp/pi-jev-tui-check.py`と`/tmp/pi-jev-tui-fixture.ts`で実Pi0.87.1 CLIをPTY起動し、tool-call-markers0.3.8併用のnormal/queued/auto/nativeと各resumeの計8ケース成功。Ctrl+O、30/80列、複数手動スキル、隣接readのマーカーgrouping、保存履歴からの再表示を確認。証拠は`/tmp/pi-jev-tui-bhfan2ho`（normal）、`...-ib37za5l`（queued）、`...-g4du7it7`（auto）、`...-dcc6kthy`（native）のANSIログ・画面スナップショット・合成イベントログ。
  - TUIハーネス初期の終了処理timeoutを修正後、上記8ケースは終了コード0。診断用psはSafehouseで拒否されたため迂回せず、以後は自身のPopenハンドルで終了・回収した。初回control検証プロセスの終了状態は未確認。セキュリティ設定は変更していない。
  - ローカル実装完了時点ではキーなしでlive未実施だった。その後ユーザーが実API検証を承認し、起動元fishから渡した環境変数を使って再開した。キーの有無だけを確認し、値の表示・保存・secretファイル参照は行っていない。公開/本番切替は未実施。元tool descriptionとpackage参照は維持。rollback元はsubagents `git:github.com/ryonakae/pi-subagents` / `ea5fb93a9ee9892be405c6a8f9b12687fbc7d090`、inline `npm:@tifan/pi-inline-skills` 1.0.6。
  - 作業中にdotfiles cwdで誤実行されたBunテスト由来の`node_modules/.vitest/.vitest-secret-token`は、作業開始時に存在しなかった生成物と確認し、内容を読まず当該ファイルと空ディレクトリだけ除去した。その後、再び未追跡`node_modules/`が現れている。新しい内容の所有者・出自は未確認であり、同じ生成物とみなして削除しない。
  - 同時にupstream版とfork版をロードしない。テスト用設定で元のユーザー設定や認証ファイルをコピーしない。
  - 検証後、公開・commit/pushに必要な承認とユーザー操作を済ませてから、`config/.pi/agent/settings.json`の`npm:@tifan/pi-inline-skills`だけをforkのGit sourceへ置き換える。subagentsのsourceは維持し、新コードを含むrefへ更新する。
  - 置換前のpackage source/refを記録し、Jevオフで戻せる経路と、元のパッケージへ戻す経路を明記する。キャッシュcheckoutやnode_modulesを手編集して検証済み扱いにしない。
  - 本番切替前に、以下のリリース制約を満たしているか確認する。

## Execution and Release Constraints

- subagentsの`AGENTS.md`はcommit禁止、明示依頼のないpush/tag/branch作成禁止。implementスキルの自動commit/push手順と競合するため、このrepoの制約を優先し、必要な解除はユーザーへ明示確認する。
- 独立repoのGitHub作成・公開範囲・pushも実行直前に承認範囲を確認する。npm publishは不要。元作者の履歴を持つ新repoの作成と、既存repoの履歴書換えを混同しない。
- 現在のNodeは22.14.0、`config/.config/mise/config.toml`にも固定されている。既存パッケージの要件に合わせ、検証環境にはNode >=22.19を用意する。グローバルpinを無断変更しない。利用するPi 0.87.1と各repoのdev依存版差も確認し、型エラー回避のために機能を削らない。
- 自動テストに実キーを使わない。live Jev確認は合成した非機密の日本語task/会話で行い、実施承認・利用可能なキー・対応Node環境を前提とする。未実施ならその範囲を残し、実測の精度/遅延改善を主張しない。
- Safehouseで拒否される操作を迂回しない。許可範囲の変更が必要なら停止して相談する。

## 修正cycle 2の承認と残るリリース判断

- ユーザーが追加1 cycleを承認。対象はsubagentsのcaller側中断確認、inline通常予約の別入力流用、不正Jev設定の警告欠落。公開・切替・commit/pushの承認は含まない。
- 以下はcycle 1停止時の記録: 次の1 cycleで、subagentsのcaller側中断確認とinline通常予約の別入力流用を修正する承認。前者は既存findingの未解消、後者はcorrection起因の新highなので、自動で修正を重ねない。
- 代案は今回の受入範囲をローカル試作までに絞り、Jev導入・fork切替を見送って現行拡張を維持すること。現在すでに両Jevはoffで、現行拡張のまま。
- cycle 2後、ユーザーはinlineの再設計を選択し、Q22で本計画の改訂を承認した。採用方式は本改訂のImplementation Decisionsを正本とし、相関情報の入力埋込みやPi本体変更の検討へ戻らない。改訂後の実装開始もユーザーの「ok」で承認済み。公開等の承認とは区別する。
- 実装・独立レビュー後の修正cycleで既存findingが未解消、または新たなhighが出た場合は、自動で修正を重ねず停止して承認を求める。新しい公開仕様・設計判断が必要な場合も同様。
- 不正Jev設定の警告欠落はcycle 2で解消。live通信はその後のユーザー承認により合成データの検証に限って実施。公開・commit/push・切替は引き続き別途承認が必要。
- 未完了のためPlanはarchiveしない。他者のClaude/Herdr/Zed/Pi設定変更は保持し、stagingもしない。

## Final Validation

- [x] **subagentsの既存契約と新規選択**: `npm run check` → lint/typecheck/全テスト成功。明示/固定/片方指定/両方指定/候補0・1・複数/対象外モデル/非対応effort/棄権/低confidence/不正応答/timeout/abort/再開を検証。オフ・両項目固定・再開ではHTTP要求0件。
- [x] **説明と設定の一致**: `tool-description-mode`/settingsテスト → ユーザーが編集したguideがJev入力・親向け説明に反映され、on/offで矛盾しない。guide欠落・不正JSON・不正candidateで安全に戻る。既存プレースホルダーと他設定の保存を壊さない。
- [x] **実効設定の表示とWorkflow**: 既存workflow/agent表示テスト → Jev選択値を起動結果へ反映し、既存の定義/呼び出し優先順位、resume、scope判定を維持する。
- [x] **子識別の並行性**: child-contextテスト＋両拡張の統合ハーネス → 同時のmain処理を子と誤認せず、子およびmention用cloneからのskill判定HTTPは0件。旧版組合せで黙って子自動選択を有効化しない。
- [x] **inline-skillsの品質チェック**: `/Users/ryo.nakae/Dev/private/pi-inline-skills`をcwdに`bun run format:check`、`bun run lint`、`bun run typecheck`、`bun test` → 全成功。明示＋自動、除外名、disable-model-invocation、低noul、ファイル読込失敗、branch/switch/reload/compaction、read成否/symlinkを含む。認証・実global設定を参照しない空の一時agentDirを使う。
- [x] **手動挿入と入力対応**: repo内のPi 0.87.1/faux providerテスト → 認証失敗/モデル未選択後のnative skill・template入力に以前の本文を混ぜない。steer/follow-up、all-at-once、同一文字列の別入力、queue clear、provider retry/error、tool error、abortで、実消費済み依頼に必要な本文を要求へ1回だけ渡し、保存・表示を重複させない。Jev失敗時にも手動挿入を維持する。
- [x] **展開と判定対象**: native展開、複数skill block、展開無効、仮想/更新後template、slash先頭template、他拡張のsendUserMessageを実SDKで確認 → Piの展開を再実行せず、最終的な依頼部分の手動指定を処理する。skill本文内のslash記述を追加の手動指定にしない。
- [x] **自動選定・read・寿命**: fetchを偽装し実拡張をロードするテスト → 同一batchのHTTPは最大1件、retryでも増えない。推薦直後は未ロードで本文も未挿入、実read成功後だけロード済みになる。readしない/失敗するモデルでも擬似履歴や強制ロードを作らない。後続入力・中断・実行終了・branch/session変更で古い推薦を破棄し、Jev待機中の無効化はpost-awaitでも検出する。
- [x] **分岐とセッション**: 実SDKのbranch/fork/switch/reload/compactionとruntime replacementを伴うnewSession → 放棄branchのロード済み状態・一時保存dedup・推薦を新branch/sessionへ引き継がない。既存の履歴復元と中断/失敗時の当該ターン保存を維持する。別AgentSession作成だけでruntime replacementも確認済みとしない。
- [x] **送信境界**: fetch捕捉テスト → current/historyの先頭・連続・途中・不正skill block、custom/toolResult/thinking/画像を送らない。テンプレート展開本文と他拡張由来の元userメッセージは承認範囲として送る。現在入力を重複させず、直前assistantと会話上限・UTF-8リクエスト上限を守る。親会話はsubagent選択へ追加しない。キーはヘッダーのみ、未知APIエラー本文・task・会話は診断へ出さない。
- [x] **組合せ統合**: `/tmp/pi-jev-sdk-integration.ts`相当のハーネスを新経路に更新し、実extensionロードと偽HTTP/providerで両off/modelのみ/skillのみ/両onを実行 → 主従識別、固定値/継承、選定件数、明示ロードを維持。auto側は偽mainモデルの標準read tool callを実行して初めて本文が入ることを確認。旧自動挿入の期待値をそのまま合格基準にしない。
- [x] **表示互換性**: 隔離したPi 0.87.1にforkと導入中tool-call-markers 0.3.8を読み込み、合成SKILL.mdと偽providerで実TUIを確認 → 通常手動は応答前、queued手動はターン終了時に既存の折りたたみ表示。native skillと実readの表示、Ctrl+O、複数スキル、隣接ツールgrouping、30/80列、履歴再表示が崩れない。prototypeへの新patchや偽tool rowは追加しない。実TUIを確認できなければ未検証として残し、コンポーネントテストだけで代用済みとしない。
- [x] **配布と履歴（初回のみ）**: 切出し履歴・基点commit・LICENSE本文・npm配布manifestをレビュー。`npm pack --dry-run --ignore-scripts` → src/README/LICENSEが入り、秘密・調査用ファイルが入らない。rootへの壊れたsymlinkがない。
- [x] **subagents必須追加チェック**: `npm run test:e2e`（偽provider、live設定なし）、`npm run build` → 成功。対象repo指示に従い、新規テストの主要assertionは対応処理を一時的に破って失敗を確認し、復元後に再検証する。
- [ ] **dotfilesと移行（初回のみ）**: 変更JSONのparse、`fish -n config/.config/fish/functions/__safehouse_args.fish`、新規symlinkの確認、package一覧と差分レビュー → 候補表の転記漏れなし、forkだけがロードされ、既存の無関係な変更を保持。実キーを表示せず環境変数の有無だけ確認する。
- [x] **日本語live確認（承認後）**: 合成ケースの実行と採択/棄権の記録を完了。実選定が有用だったことまで一律に合格とは扱わない。閾値・本番設定は変更していない。結果は次節。
- [x] **最終レビュー**: 実装担当とは独立したレビューで入力対応・本文/指示の寿命・プライバシー・既存表示を確認する。有効な結果と差分を照合し、初期設定値、Jevオフ時の回帰、未実行のlive/公開/切替を報告する。subagentsのcycle 2のcheck/e2e/build・独立レビュー結果は、そのコードや共有契約に新たな変更がなければ再利用する。旧inline統合結果は新方式の合格に流用しない。本番切替は別途承認後のみ。

## 実Jev検証結果

- 承認: ユーザーの「本当のjevで検証してくれていいですよ」、キー受け渡し後の「実Jevの検証を続けて」。対象は合成タスク/会話。Jev以外のモデル実行はfaux providerで、本番認証・モデルの実起動は未検証。
- 初回`/tmp/pi-jev-live-check.ts`: 本物のselector/clientと20候補、既定5秒・confidence 0.7・noul 0.85を使用。ただし後続確認で、モデル側のguideを`loadModelSelectionGuides`に通さずMarkdown原文を渡していたハーネス不備を発見。placeholderとbenchmark共通metadataの展開条件が実装経路と異なるため、初回モデル結果は参考値とし、下記で再確認した。利用可能model registryのみfixtureで、実アカウントの候補利用可否を検証したものではない。キーはenvから取得しヘッダーにのみ使用。保存結果は`/tmp/pi-jev-live-6BthMD/results.json`（疎通）と`/tmp/pi-jev-live-G9apNr/results.json`（代表例）。最初のmatrix実行はハーネスの旧getModel参照でHTTP送信前に失敗し、fixture registryへ修正した（repo変更なし、`/tmp/pi-jev-live-dA4DXI/results.json`）。
- スキル5例: docs照会→find-docs 0.96、短い了承＋直前の回帰テスト提案→tdd 0.91、挨拶→選定なし、手動tdd＋React公式仕様→find-docs 0.93、計画だけ/実装禁止→選定なし。事前に用意した期待を5/5で満たした。ただし候補を3種に絞った合成ケースであり、実際の全スキル集合に対する精度保証ではない。除外対象は候補へ提供していない。
- 初回モデル4例（guide条件に上記不備あり）: 定型調査はconfidence 0.35でfallback、複数箇所の修正は棄権（0.15）、並行性/認可設計レビューは棄権（0.19）、Sol固定でeffort選択はconfidence 0.46でfallback。両固定はHTTP 0件で固定値維持。
- 原因確認の再検証 `/tmp/pi-jev-model-diagnosis.ts`: 実際の`loadModelSelectionGuides(...).selectionGuide`を使用、4 HTTPとも200。定型調査はLuna/low（probability 0.56、confidence 0.52）、Sol固定はmedium（0.62、0.53）を選んだが閾値0.7でfallback。複数箇所修正はabstainとSol/xhighが各0.13、Sol/highが0.12で分散し、abstain選択（confidence 0.08）。設計レビューはabstain 0.20、Astra/high 0.12、Astra/medium 0.10、Sol/high 0.09でabstain選択（confidence 0.16）。両固定は再びHTTP 0件。記録 `/tmp/pi-jev-live-ytPt81/results.json`。正しいguide生成経路でも採択0/4だった。
- 解釈: 低confidenceによる棄却2件、abstain選択2件という直接原因は確認できた。20組合せ＋abstain、候補ごとの用途説明なし、広い合成タスク、情報不足時には棄権するguideが判断を難しくした可能性があるが、どれが主因かの比較実験は未実施。confidenceとprobabilityは別の返却値であり、成功率とも同一視しない。初回との差をguide修正だけの効果と断定しない。設定・閾値は未変更。
- `/tmp/pi-jev-live-sdk.ts`: 隔離Pi SDKへ両forkを実ロード、model側off/skill側on。実Jevがread指示を生成したことをassertし、faux mainの標準readで初めて本文を取得、その後Agent子を起動。Jevはmainの1回だけ、子判定はmain=false/child=true、子へのスキル本文転送なし。結果はPASS、証拠root `/var/folders/55/dc4z6w01287dbgs2kk_5c0mc0000gp/T/pi-jev-sdk-0sjUNX`。
- 初回10 HTTPと原因確認の追加4 HTTPがすべて200。観測遅延は約153〜257ms（各ケース少数測定、改善率や将来の上限を保証しない）。生APIエラー本文・キーはログへ保存せず、分類・スコア・HTTP status・遅延のみ記録。
- 用途説明比較（ユーザーの「それで進めてみるか」に基づく実験）: `/tmp/pi-jev-candidate-profiles.json`に20組合せの説明を用意し、`/tmp/pi-jev-description-comparison.ts`でdescriptionの有無だけを変えて実Jevへ送信。guide・候補数・benchmark・閾値0.7・timeout5秒は固定、各タスクで実行順を交互にした。能力の実証ではなく運用仮説として記述し、候補を減らしたり特定候補を強制したりしていない。結果と事前protocolは`/tmp/pi-jev-description-yVwetp/`。
  - 定型調査: 現行0.44でfallback → 説明付きLuna/low、0.91で採用。
  - 複数箇所修正: 現行abstain、0.10 → 説明付きSol/high、0.89で採用。
  - 並行性/認可レビュー: 現行abstain、0.16 → 説明付きAstra/high、0.78で採用。
  - Sol固定の小修正: 現行0.48でfallback → 説明付きSol/medium、0.80で採用。固定modelを維持。
  - 既知4タスク各1回では、採択は現行0/4、説明付き4/4。ただし説明作成時に既知のタスクを見ており、過適合の可能性を除けない。confidenceの上昇を実タスク成功率の上昇とは扱わない。
- 説明を固定した追加holdout比較: `...comparison.ts --holdout`、記録`/tmp/pi-jev-description-NVnuj7/`。
  - 仕様と自動検証が揃った変換機能追加、費用優先: 現行はLuna/low confidence 0.14、説明付きはLuna/high 0.27でどちらもfallback。説明付きのprobabilityはLuna/high 0.30、Luna/max 0.24に分散し、effortの境界は未解消。
  - 対象/目的/完了条件が未定の依頼: 両方abstain。説明付きconfidence 0.97（現行0.93）で、何でも採択する挙動にはなっていない。
  - 比較計12 HTTPすべて200、観測遅延154〜270ms。用途説明は`/tmp`だけで、repoコード・設定のcandidate description・閾値・両off・本番package参照は未変更。
- 判定: スキル側は実Jev→実extension→標準readの経路を確認。モデル側は用途説明の追加が採択を改善する兆候を得たが、未見タスクでの安定性・費用重視時のeffort選定・実行品質は未確認。本番導入、実モデル認証/起動、長期的な日本語精度は未検証。用途説明の正式反映や他の調整、本番切替は別途合意してから行う。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま `docs/plans/archived/` へ移す。
