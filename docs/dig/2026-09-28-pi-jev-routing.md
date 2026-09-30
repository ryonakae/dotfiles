# dig log: Pi の Jev モデル選択・スキル連携

## 導入完了時の記録

以下の設計・検証経緯には当時の未承認・未導入状態を残す。現在の運用はこの節と[README](../../README.md#pi-の-jev-連携)を参照する。

- 後続の個別承認により、自動本文挿入を`6b601ae`でcommit/push・導入済み。[完了計画](../plans/archived/2026-09-30-pi-inline-skills-auto-injection.md)に検証結果を記録した。
- 両forkを履歴の書き換えなしで`master`へ統合し、GitHubのdefault branchとdotfilesのpackage参照を揃えた。README更新後の導入commitはsubagents `d2a493d`、inline-skills `9491b98`。検証済みfeature branchとの差分はREADMEだけ。ユーザーがreload完了を確認した。
- 両JevはTypeSafeで有効。スキルの`excludedSkills`は`[]`。スキル本文のロードは各スキルの実行条件や操作の承認を解除しない。
- 導入後の通常Agent試行では、Jev confidence `0.650`が閾値`0.7`未満で子を起動せず親判断へ戻った。親がLuna / mediumを指定して再呼び出し、README要約を8.5秒で完了した。この時間はJev待機込みではなく、自動選定による高速化・精度・費用改善は未計測。
- 実OpenRouter接続は未検証。候補の用途説明を加えた実験は本番設定に反映していない。

## 目的・前提・制約
- Jev を現在の Pi 運用に組み込み、サブエージェントの model/effort 選択とスキル連携に利用する。
- 現在は git:github.com/ryonakae/pi-subagents と npm:@tifan/pi-inline-skills を利用している。
- ryonakae/pi-subagents は tintinweb/pi-subagents の fork。作業用リポジトリは /Users/ryo.nakae/Dev/private/pi-subagents。
- @tifan/pi-inline-skills の upstream は tifandotme/pi-extensions 内のパッケージ。
- 現行モデル候補は openai-codex の gpt-5.6-luna / gpt-5.6-terra / gpt-5.6-sol / gpt-6-astra。
- 調査時の Node は 22.14.0。既存パッケージの一部は >=22.19.0 を要求する。
- Jev は外部の分類・選択 API。日本語精度、送信データ、障害時の挙動を設計する必要がある。
- dotfiles に既存の未コミット変更がある。今回の作業で上書きしない。
- 設計合意後にplanを保存し、計画承認後に実装する。初期実装・修正cycle 2・inline-skillsの入力対応再設計・モデル選定フォールバック再設計までローカル実装と検証を完了。本番切替・公開は別途承認待ち。
- 再開時の履歴は、参照可能な会話・圧縮要約・既存dig log・実装計画に基づく。圧縮前の逐語記録がない部分は補完しない。

## 決定事項
- ryonakae/pi-subagents に Jev によるサブエージェントの model/effort 選択機能を追加する。
  - 出典: ユーザーの今回の依頼。
- @tifan/pi-inline-skills を fork して Jev 機能を追加し、既存の同パッケージを fork 版で置き換える。
  - 出典: ユーザーの今回の依頼。

- サブエージェントの model / effort は未指定項目だけ Jev が選ぶ。呼び出し時の明示指定・agent 定義の固定値は維持する。
  - 理由: 既存の呼び出しを壊さず、自動選択と固定指定を併用する。
  - 出典: Q1 でユーザーが A を選択。

- モデル選択のために Jev へ送る情報は、委譲タスク本文・agent の役割説明・モデル候補と選択基準に限定する。親の直近会話は追加送信せず、事前の要約処理も行わない。
  - 注意: タスク本文に含まれるコードや機密情報は送信対象になる。
  - 理由: 単独で理解できる委譲タスクを用意する既存方針に合わせ、追加の会話送信と要約処理を避ける。
  - 出典: Q2 でユーザーが A を選択。

- モデル選択でJevが選べなかった場合は、未指定項目を親エージェントが判断して決める。親のmodel/effortの単純継承で即起動する旧Q3の方式は置換する。
  - 出典: 実Jev検証後の「jevで選べない場合はあなたがmodel/effortを選ぶんだと思ってた」、および「未指定のサブエージェントに対しては、jevが判断 -> 無理なら親エージェントが判断」。
  - サブエージェント定義の固定値は最優先で維持し、未指定項目だけを補う。両方固定ならJevや親の再選定は不要。片方だけ固定の場合も固定部分を変えない。
  - 2026-09-29の親選定計画に基づきローカル実装・検証済み。本番パッケージは未切替で両Jev offのため、運用環境へ反映済みとは扱わない。

- model / effort は必要な品質を満たす範囲で、時間・費用のバランスを取って選ぶ。model と effort を組み合わせて比較する。
  - 既存ベンチマークは参考情報として使い、個別タスクの品質保証として扱わない。
  - 理由: 現在の選定方針を引き継ぎ、モデル単価だけでなく完了までの時間・総費用を考慮する。
  - 出典: Q4 でユーザーが A を選択。

- inline-skills は既存の `/skill名` による明示ロードを残し、依頼文から Jev が必要なスキルを選ぶ。当初の本文自動挿入はQ18で標準readへの指示に置換した。
  - 明示的に依頼された場合のみ使うスキルは自動選択対象から除外する。低信頼度では自動推薦しない。
  - 理由: スキル指定の手間を減らしつつ、明示依頼を要するスキルの利用条件を守る。
  - 出典: Q5 でユーザーが A を選択。

- メインモデルに渡す skills catalog は維持する。Jev が選び漏れた場合もメインモデルが一覧から追加ロードできる構成にする。
  - 理由: 日本語の依頼や複数スキルが必要な作業での選択漏れに備え、自動選択の精度を確認してから削減を検討する。
  - 出典: Q6 でユーザーが A を選択。

- 明示依頼専用スキルは設定の除外リストにスキル名を列挙し、コードで Jev の自動選択対象から確実に除外する。説明文の都度解釈には依存しない。
  - 初期リストは既存スキルの利用条件から整理する。`/skill名` による明示ロードは維持する。
  - 理由: commit-push・implement・doc-updater 等の利用条件を、分類の誤判定に左右されず守る。
  - 出典: Q7 でユーザーが A を選択。

- スキルの Jev 自動選択はメインセッションだけに適用し、サブエージェント内では実行しない。サブエージェント側の既存のスキル一覧・必要に応じた読み込みは維持する。
  - 理由: まず適用範囲を限定し、委譲先ごとの外部送信・待ち時間・ロード量の増加を避ける。
  - 出典: Q8 でユーザーが A を選択。

- スキル選択には今回の依頼文、直前の assistant 発言を含む上限付きの直近 user/assistant 会話、候補スキルの名前・説明を Jev に送る。
  - tool result・thinking・展開済みスキル本文・添付内容は含めない。
  - 理由: 「実装しますか？」「お願いします」のようなやり取りでも、会話上の意図を踏まえて選択するため。
  - サブエージェントのモデル選択には単独で理解できる委譲タスクを渡すため、Q2 の送信範囲は維持する。
  - 出典: Q9 の文脈不足に関するユーザー指摘と、修正版 Q9 での A 選択。

- `/skill名` を明示したターンでも Jev の自動選択を行う。指定スキルは必ずロードし、それに加えて Jev が補助スキルを選ぶ。
  - 明示依頼専用スキルの除外は自動選択にのみ適用し、明示ロードを妨げない。
  - 出典: Q10 でユーザーが B を選択。

- 両拡張は TypeSafe 公式 API へ直接接続し、同じ API キーを使う。Vercel AI Gateway や MCP adapter を実行時の必須依存にはしない。
  - キーをコードや Git 管理ファイルに保存しない。
  - 理由: 経由サービスや拡張間の実行時依存を増やさない。
  - 出典: Q11 でユーザーが A を選択。

- inline-skills は tifandotme/pi-extensions から対象パッケージを履歴・ライセンス付きで切り出し、ryonakae/pi-inline-skills として独立管理する。
  - upstream の対象パッケージへの変更を取り込む運用とし、出自と追随方法を記録する。
  - 理由: Pi への導入対象を明確にし、使わない拡張を管理対象に含めない。
  - 出典: Q12 でユーザーが A を選択。

- 両拡張に設定による Jev のオン・オフを設ける。
  - オフの場合は Jev へ通信せず、subagents は従来の model/effort 解決、inline-skills は従来の明示ロードと関連機能を維持する。
  - 出典: Q13 に対するユーザーの追加要望。

- modelSelectionGuide の説明文もユーザーが後から編集できるよう、dotfiles で管理する。ユーザーの選定方針やオン時の案内を拡張コードに固定しない。
  - 出典: modelSelectionGuide の定義場所についての説明後、ユーザーが dotfiles 管理を明示的に希望。

- 最終のMarkdown管理構成をユーザーが「それでいこう」と承認。その後、[実装計画](../plans/2026-09-28-pi-jev-routing.md) に対して「実装して」と依頼した。
  - 新規ローカルリポジトリはすべて `/Users/ryo.nakae/Dev/private` 以下に置く。
  - 実装・検証は承認済み。公開・push・本番切替の承認範囲は計画に従う。
  - 以下の設計途中の未決事項・提案は、最終実装計画の内容を優先する。

- inline-skillsを保留してsubagentsだけ先行する案ではなく、入力対応方式の再設計を進める。
  - 出典: 修正cycle 2の報告に対するユーザーの「設計し直しで」。
  - 入力への識別子追加・対応範囲の縮小は承認されていない。
- Pi本体は変更せず、拡張内で完結する方式を設計する。必要な保存形式・表示の変更を個別に検討する。
  - 出典: Q14でユーザーがBを選択。
  - Pi本体のforkや公開API追加は今回の対象外。保存形式・表示の具体的な変更まで包括的に承認されたわけではない。

- スキル呼び出しはPi標準機能に近い挙動を希望する。単なるユーザーメッセージ末尾への本文追加ではなく、標準の展開・履歴保存・折りたたみ表示を設計の基準にする。
  - 出典: Q15に対する「piの標準機能でスキルを呼び出した時みたいな挙動がいい」。A/Bの単純選択とは扱わず、具体的な表示変更への包括承認と解釈しない。

- Jevの現在入力には、プロンプトテンプレート展開後の依頼文を渡してよい。テンプレート本文と差し込み引数も送信対象になる。
  - 出典: Q16でユーザーがAを選択。
  - 展開されたSKILL.md本文・添付・tool result・thinkingは引き続き除外する。直近会話の上限とリクエスト上限は維持する。入力対応方式自体を承認したものではない。

- 表示は導入中のtool-call-markers等の拡張と正しく共存することを優先する。複数スキルのまとめ方だけを独立に決めない。
  - 出典: Q17に対する「tool-call-markers みたいな拡張機能も使ってるから、それで正しく表示されるやつ」。A/Bの表示粒度はいずれも明示選択されていない。

- 既存表示拡張との互換性を受け入れ条件として、再設計を続行する。
  - 出典: 互換性条件の記録に対するユーザーの「それで進めて」。未確定方式の実装・本番切替を包括承認したものとは扱わない。

- Jevによる自動選択後のスキル本文は、メインモデルに標準のreadで読み込ませる。拡張による本文の直接挿入は行わない。
  - 出典: Q18でユーザーがAを選択。
  - モデル実行前に必ず本文をロードする保証はなく、モデルが読み込み指示に従う必要がある。実際のread結果を表示・履歴・ロード済み判定に使い、擬似tool call/resultは作らない。
  - この変更はJevの自動選択に限る。手動の`/skill名`はQ19で直接挿入の維持が決定。Pi標準の`/skill:名前`とも区別する。
- 拡張の手動`/skill名`は従来どおり本文を直接挿入する。Jevによる自動選択だけを標準readへの指示にする。
  - 出典: Q19に対する「今のinline-skillsはBか？じゃあBがいいな」。手動/自動/nativeの分離説明に対してユーザーが「ok」と確認。
  - 導入中upstream版は`input`で本文を読み、`before_agent_start`で`inline-skills` custom messageを挿入する（installed `src/index.ts:577-643`）。現在のupstream版にJev自動選択があるという意味ではない。
  - 手動の直接挿入・既存表示は維持するが、既知の別入力への流用を許容する承認ではない。旧予約処理をそのまま残すかどうかは別の実装判断。Pi標準の`/skill:名前`は変更しない。

- 手動スキルを含む実行中の追加入力（steer/follow-up）は、本文を応答前にモデルへ渡し、折りたたみ表示・履歴保存はターン終了時に行う。通常入力の即時表示は維持する。
  - 出典: Q20に対する「Bは可能なの？無理ならAで」。確認済みの公開APIではBを安全に実現する方法が見つかっていないため、今回の公開API限定条件下ではAを採用する。
  - Bの数学的な不可能性を証明したわけではない。内部API/表示へのpatchやPi本体変更を許可したものとは扱わない。
  - その説明とAの適用範囲に対し、ユーザーが「ok, 進めて」と確認。残る境界の設計検証を続行する。

- スキル判定を実際に実行されるuserメッセージに統一する。テンプレート展開後の本文と、他拡張が生成したuserメッセージも対象とする。
  - 出典: Q21でユーザーがAを選択。
  - 他拡張由来の依頼もJevへの送信対象になり、その中の`/skill名`も明示指定として扱う。Q16のテンプレート本文送信承認に加え、入力元による旧除外を廃止する。
  - userメッセージ扱いはprovider変換前の型に基づく。custom/toolResult/thinking/添付/展開済みskill本文の除外、会話・リクエストサイズ上限、メインセッション限定、明示依頼専用スキルの自動選択除外は維持する。

## モデル選択フォールバックの再設計

- 2026-09-29: ユーザーの「その方針で修正」に基づき経路を調査し、[親選定計画](../plans/2026-09-29-pi-parent-model-selection.md)を提示。その後の「ok」で計画と実装開始を承認。ローカル実装・全体check（2213 pass/7 skip）・実Pi SDKの2経路・独立レビュー（指摘なし）が完了。新しい契約と検証・進捗は同計画を正本とする。commit/push/本番切替/公開/archiveは引き続き対象外。
- 通常Agentは起動前に選定要求をツール結果として返し、親が既存のmodel/thinking引数で再呼び出す。Workflowは同じrun内で該当agentを待機させ、元の親へ通知して`SubagentWorkflow`の`action:"route"`で選定結果を受け取る。完了済み作業を再実行する可能性があるjournal再開は、この待機の解除に使わない。

- サブエージェント定義を優先し、未指定値はJev、不採用なら親が判断する意図を確認。フォールバックは「親の値を使う」ではなく「親がタスクを評価して指定する」。Jevから選択候補が返っても低confidenceで不採用ならこの経路に入る。ユーザー中断を親への再選定依頼として続行しない原則は維持する。
- 再設計調査時の優先順位: Agentの`resolveAgentInvocationConfig`は定義 > 呼び出し引数だが、Workflow hostは呼び出し引数 > 定義だった。今回の「定義済みなら問答無用でそれを使う」に合わせ、両入口で定義優先に揃える必要がある。定義modelが解決不能なときの既存の黙った親継承も、固定値維持と矛盾しない扱いへ詰める。
- 親はJev不採用の後に判断する。子の起動を保留し、親が未指定値を選んでから起動する順序は、直前の3段階の説明に対するユーザーの「そうです」で確認済み。親が毎回予備候補を事前計算する方式へ読み替えない。判断要求APIとWorkflowの同一run継続は2026-09-29の計画で承認。検証結果は同計画に記録する。
- 親選定計画で確認した対象: 呼び出しで明示された値とJevの関係、Jevオフ時の従来動作、候補なし/不正定義/未対応model/認証・通信障害時の親判断、Workflow内で既に完了・進行した仕事を重複実行しないこと。これらは2026-09-29の親選定計画で実装・検証した。本番off・公開等の制約を維持する。

## 再設計の確認事項・未決
- subagents側のcaller abort確認と不正Jev設定警告は修正・独立レビュー通過。check 2192 pass / 7 skip、e2e 68 pass / 7 skip、build成功。本番未切替、commit/pushなし、両Jevはoff。
- inline-skillsは認証preflight失敗した`/alpha`の予約が残り、後続`/skill:beta next`または`/template next`へalpha本文が混入することを実Pi 0.87.1/faux providerで再現。既存37テストは成功するが、新しい再現テスト2件は失敗。証拠は`/tmp/pi-inline-cycle2.8MJt6D/`。
- 公開InputEventとBeforeAgentStartEventに共通入力IDはない。通常入力ではinput→skill/template展開→model/auth確認→before_agent_startの順。preflight失敗は呼び出し元へ返り、拡張への専用通知はない。idle時のctx.signalも常時利用可能とは限らない。
- 現在の予約方式で、失敗済み入力と同時進行中入力を確実に区別する修正は未成立。FIFO、不一致時に先頭を選ぶ処理、無条件の全消去を安全な対応付けとみなさない。
- 未合意の調査候補: (1) 入力受付時の予約をやめ、通常入力のbefore_agent_startとqueued入力の実消費境界で選定・挿入する、(2) 入力へ相関情報を付ける、(3) Pi側に公開入力ID/失敗通知を追加する案はQ14で対象外になった。(1)(2)の実現可能性・送信内容・既存UI/展開/履歴への影響を確認する。
- 方式(1)では実行対象の展開後入力を扱う可能性がある。template展開後の送信はQ16で承認済み。標準skill本文の除外、queued境界の同時性/中断/出自、表示タイミングの実現可能性は引き続き確認する。
- 追加調査: `turn_end.context.pendingMessages`はqueue消費前のsnapshot。非同期handler待機中にsteerが追加されるとfollow-upより先に消費され得るため、このsnapshotだけでは同一入力との対応を保証できない（Pi `agent-session.js:350-475`、agent-core `agent-loop.js:179-186`）。
- 追加調査: 公開`message_end`は実際に消費されたmessageを扱い、同一roleの置換を返せる。Piはlistenerをawaitし、置換したmessageを状態・履歴へ反映する（`agent-session.js:694-764`、agent-core `agent.js:429-430`）。ただし独立custom messageの追加は返せず、この案はスキル本文を含むユーザーメッセージへ保存形式・表示を変更する可能性がある。採用も実動検証も未実施。
- 追加調査: `context`での本文追加はprovider要求内だけの変換で、従来のcustom messageとして履歴へ残らない。入力sourceもdownstream user messageには保存されない。既存の永続表示・branch単位ロード管理をそのまま維持できると断定しない。
- Q14はBで決定。次の候補は、実際に消費されたuser messageの`message_end`で選定し、その同じmessageへ本文を追加して返す方式。別イベントへ選択結果を渡す予約を不要にする方向。元の依頼文・添付は保持し、拡張の追加本文を区別する。ただし実動検証・採用は未実施。
- Q15回答: Pi標準のスキル呼び出しに近い挙動を希望。標準は`<skill name="..." location="...">本文</skill>`の後ろに依頼文を付け、1つのuser messageとして保存する。TUIは先頭skill blockを折りたたみ表示し、依頼文は別表示する（Pi0.87.1 `agent-session.js:1365-1378`、`interactive-mode.js:3076-3091`、`skill-invocation-message.js`）。標準parser/UIは1つの先頭skill blockを扱うため、複数スキルの見せ方は未決。
- 新たな制約: TUIはuserの`message_start`で表示し、userの`message_end`を無視する（`interactive-mode.js:2724-2733,2768-2770`）。したがってmessage_end置換だけでは、履歴を変更できてもその場の標準表示は更新されない。前の候補を実現済み・採用済みとは扱わず、表示タイミングを含め再検討する。
- Q16はAで決定。送信範囲の承認を、標準に近い即時表示や入力対応方式の実現可能性の確認とは区別する。
- Q17回答: 見た目のA/B選択より既存表示拡張との互換性を優先。表示粒度は保留し、実装候補と実表示検証に基づいて判断する。自動選択の件数を減らす承認ではない。
- 導入中の`@pi-kaush/pi-tool-call-markers`は0.3.8（`config/.pi/agent/settings.json`のnpm参照とinstalled package.jsonを確認）。README全文・実装を確認。同拡張の対象判定は`ToolExecutionComponent`（`src/index.ts:445-449`）。`read`のcall rendererの見出しとして`read`と`[skill]`を認識する（`:802-807`）。標準`/skill:name`展開の`SkillInvocationMessageComponent`は別経路であり、同拡張がすべてのスキルロードをtool rowとして描くわけではない。
- 互換性検証案: tool-call-markers有効状態で標準read/標準skill展開/新しい自動ロードを区別し、通常・展開表示、複数スキル、隣接ツールのgrouping、履歴再表示を確認する。静的確認だけで表示互換性確認済みとはしない。マーカー表示のためだけに未実行のreadや擬似tool call/resultを履歴へ作らない。
- 追加の実証候補: input handler内で判定から本文構築までを完了し、その入力自身のtransform.textとして返す。後のイベントへ予約結果を受け渡さない。native skill/templateを公開APIで正しく扱えるか、preflight失敗・queue順序・同時入力で取り違えないかを/tmpの偽providerハーネスで確認する。repoコードは変更しない。
- 入力transform実証: `/tmp/pi-input-transform-proof.test.ts`、実Pi0.87.1/faux providerで13 pass / 54 assertions。本文を入力自身の戻り値に含めるとpreflight失敗後や遅延/queued入力の取り違えは防げた。一方、queue投入は判定完了順、idle中abortではinput待機を止めず後から実行される。標準展開の維持は未成立。
- transformの制約: input eventにexpandPromptTemplatesがなく、getCommandsにはロード済みtemplate内容がない。ファイル再読込はロード後変更/仮想templateと一致せず、展開helperは公開root exportではない。先行展開による二重展開も再現。ハーネスの内部helper利用は比較用oracleのみであり、公開APIによる実装成功とは扱わない。
- 表示実証: `/tmp/pi-jev-native-skill-display.ts`でtool-call-markersの実patch・マーカー行が有効なことを確認し、標準単一skillの折りたたみ/展開が30/80列で変わらないことを確認。複数blockの単純連結は2件目本文が露出することを確認。実TUI全体・クリック・grouping・履歴画面の検証ではない。初期ハーネスのimport/クラスidentity/session_start設定は修正してから検証した。
- Q18はAで決定。Jevは選定とreadへの読み込み指示に限定する。選定指示の挿入時点・繰り返し防止・送信内容は今後詰める。Pi内部API/表示の互換アダプターを導入するBは採用しない。
- Q19はBで決定。手動指定は本文直接挿入、自動選択はread指示に分離。manual・native展開・成功readのロード済み管理はbranch単位で整合させる。自動指示を出しただけでロード済みにしない。
- 手動直接挿入の追加実証: `/tmp/pi-manual-context-proof.test.ts`、実Pi0.87.1/faux providerで5 pass / 23 assertions。通常入力は`before_agent_start.prompt`から同期的に本文を組み立て、そのイベントの戻り値にcustom messageを返す。queued入力は`context`の実消費済みuser messageから本文を組み立て、当該provider要求へ追加する。同時に`pi.sendMessage(...,{triggerTurn:false})`でcustom messageの保存・表示を予約する。この予約は入力の推測対応ではなく、消費済み依頼について確定した本文の保存である。
- 公開APIの制約: streaming中のtriggerTurn:falseは現在ターン終了まで保存・表示を遅延する（`agent-session.js:1470-1548`）。通常入力は従来の即時表示を維持できるが、queued入力の表示時点は変わる。検証では最初のprovider要求に本文が1回だけ入り、通常入力では要求前に表示・保存、queued/context方式ではassistant完了後に表示・保存されること、次入力で重複挿入しないことを確認。preflight失敗とsteer/followUpのqueue clearも確認した。
- この実証は簡略化した名前抽出と固定本文を使い、実拡張の本文読み込み・renderer・Jev・branch切替を検証したものではない。手動判定対象が展開後入力になる影響、native/template/extension由来入力の扱い、同時入力・中断・エラー時の保存、複数user messageを一括消費する場合は未検証。全体修正完了とは扱わない。
- Q20は今回の公開API限定条件下ではAを採用。ユーザーはBの可否を質問し、不可能ならAと回答。確認済みのsendCustomMessageではstreaming中に即時保存・表示する経路がなく、別の公開APIによる安全なBも未実証であることを説明した。通常入力の即時表示とqueued入力の応答前本文提供は維持し、queued入力の表示・保存のみターン終了時にする。
- 手動境界の追加実証: `/tmp/pi-manual-context-extended-proof.test.ts`、7 pass / 34 assertions（親も再実行）。all-at-onceの複数user、provider retry、provider error、abort、tool error、branch切替、新規AgentSessionを確認。本文の要求内追加と履歴保存を別管理し、消費済みsourceEntry.id集合で保存予約を重複排除する。ロード済み状態はactive branchから復元する。エラー/abort時も本文は当該ターンの履歴として保存され、次入力へ未確定予約を持ち越さない。
- 上記は固定本文の設計ハーネス。実renderer・Jev・実SKILL.md読み込み・runtime replacementによるnewSessionは未検証。新規AgentSessionを作るテストとruntime replacementを同一視しない。
- 判定対象はprovider変換後のuser roleではなく、session projection上の元user entryに限定する。custom messageもprovider変換後はuser roleになるため、変換後roleだけを見ると本文再送を招く。消費済みの複数user entryをまとめて扱い、最新1件だけに限定しない。
- Jevプライバシー検証: `/tmp/pi-jev-conversation-boundary-proof.ts`で現`conversation.ts`を展開後入力にそのまま流用すると、currentInputと2つ目のskill blockが除去されないことを確認。偽本文のみ使用、外部送信なし。本番未切替。新経路では現在入力・履歴の双方へ全skill blockの除去を適用し、不正/閉じていないblockを含む文字列は送信しない。custom/toolResult/thinking/attachmentは対象外、同じ現在入力をhistoryにも重複追加しない。
- 入力元の制約: InputEventにはsourceがあるが、BeforeAgentStartEvent/context/sourceEntryにはその情報が渡らない。sendUserMessageはsource:extension、expandPromptTemplatesの既定falseでpromptへ渡すが、消費後は元user entryになる（Pi `agent-session.js:1547-1575`）。現upstreamはinput段階でextension由来を除外しているため、消費後のuser本文を一律判定する案は対象範囲の変更になる。手動判定も展開後本文へ移るため、template内の`/skill名`をどう扱うかが関連する。
- Q21はAで決定。実消費userメッセージに統一し、template展開分と他拡張由来も含める。旧入力sourceに基づく除外は維持しない。
- 全体確認に含める提案: 自動選定は実消費済みuser entryの集合につき一度だけ。provider retryでは結果を再利用し、Jevへ再送しない。読み込み指示はその依頼の実行中に限ってprovider contextへ追加し、指示自体は履歴へ永続化しない。成功したreadで該当候補を除き、新入力・中断・実行終了・branch/session変更で破棄する。catalogは引き続き利用可能。これはモデルによるreadの強制・未読時の再選定を意味しない。
- 非同期ガードの設計条件: Jev完了後にもsignal/session generation/実消費batchを検査し、無効化済みの結果を次入力へ適用しない。Jev失敗時は自動推薦だけを省き、手動の直接挿入は維持する。中断はエラーフォールバックとして続行しない。
- Q22はAで決定。ユーザーの「a」でQ18〜Q21と選定指示の寿命を含む全体設計、計画改訂を承認。その後、改訂計画の提示と実装開始確認への「ok」により実装開始も承認された。公開・本番切替・commit/push・live APIは承認に含めない。
- 設計ツリー: Pi公開API限定 → 手動直接挿入/自動read指示の分離 → queued表示遅延 → 実消費userメッセージへの判定統一 → 選定指示の寿命を含む全体確認 → 計画改訂 → 実装承認（完了）。実装の進捗・未検証は実装計画へ記録する。

## OpenRouter対応

- ユーザーの追加要件: 両フォークでTypeSafe公式APIキーだけでなくOpenRouter APIキーも利用できるようにする。現在のコードはTypeSafeのendpointとTYPESAFE_API_KEYに固定されている。
- 公式仕様を確認: https://openrouter.ai/docs/guides/community/typesafe-sdk 。OpenRouterは`POST https://openrouter.ai/api/v1/systemone`でTypeSafe互換のstate/questions/answersを扱い、Bearer認証にOpenRouterキーを使う。Choice/Noulの既存処理を維持でき、Chat Completionsへ置換する必要はない。追加のid/provider/usageメタデータは既存の応答処理では参照しない。
- モデルID: OpenRouter公式例は`jev-1.13`または`typesafe/jev-1.13`。現在のTypeSafe既定`jev-1.13.0`がそのまま使えるとは確認できていないため、provider別の既定と明示modelの扱いを分ける。
- Q23はAで決定: 両拡張に`jev.provider: typesafe | openrouter`（省略時typesafe）を設け、接続先を設定で明示する。ユーザーは続けて環境変数以外のキー管理方法と他Pi拡張の実例を質問。provider選択の合意とキー取得元の合意を区別し、キー保存先/取得順位はまだ変更しない。
- 認証の公式確認（Pi 0.87.1 docs/providers.md、models.md、model-registry.js）: `/login`でproviderキーをauth.jsonへ保存できる。auth.jsonは暗号化ストアではなくJSON（作成mode 0600）。`key: !command`でKeychain等から取得する方法も公式対応し、結果はprocess中cacheされる。標準優先順はruntime指定 > 保存credential > models.json > 環境変数。拡張向け`ctx.modelRegistry.getApiKeyForProvider()`は標準認証解決を利用する。OpenRouterは組み込みprovider。TypeSafeを同様に扱えるかは別途確認が必要。実credentialファイルの読取や解決関数の実行はしていない。
- APIキーの実値は拡張の設定JSONやGitへ保存しない。ユーザーはPi標準認証の再利用案を承認。Keychain自体の設定・移行は今回行わない。明示off・固定値・親選定fallback・スキル手動経路・中断・タイムアウト・送信上限の意味を変えない。自動的なprovider間failoverは提案していない。
- 導入済み拡張の実例を確認（配布ソースのみ、秘密の実設定未読）: pi-web-accessの`credential-source.ts:152-191`は`$ENV`/`!command`/環境変数/設定リテラル、`page-query.ts:112`はPiのmodelRegistry認証を利用。pi-mcp-adapterの`secure-keyring.ts:32-50`はOS資格情報ストアを利用する。2例からエコシステム全体の普及率は主張しない。
- 承認済み（ユーザー「そのおすすめ案で」）: 独自のキー保存機構を増やさず、OpenRouterはPi標準認証を再利用して保存済みキー/環境変数を利用可能にする。TypeSafeは従来の環境変数を維持。保存時の保護を重視するならPi標準のコマンド参照または起動時注入でKeychain等と組み合わせる。ただし認証取得後は同じprocessの信頼済み拡張から読め、完全な秘密隔離にはならない。Safehouseからのコマンド利用可否は未検証。
- `/implement`で[OpenRouter対応計画](../plans/2026-09-30-pi-jev-openrouter.md)の実装を開始。dotfilesのSafehouse引数へOPENROUTER_API_KEYの明示passを追加し、両Jev設定にprovider: typesafeを明示。開始時コピーとの比較で他の値・off・本番package参照・sandbox権限の維持とfish構文を確認した。実キー読取/実API呼び出しは行っていない。
- 合成資格情報のPi 0.87.1 SDK検証で、runtime key > 保存credential > 環境変数を確認。初期harnessでAuthStorageのroot exportを仮定して失敗したため、公式SDK例のauthPathによる専用temporary fixtureへ修正した（製品コードの問題ではない）。証跡: `/tmp/pi-openrouter-implementation/auth-sdk.log`。
- 先行変更は両repoの`feat/jev-routing`へpush済み（subagents e2ea810、inline-skills aabcfb9）。今回のOpenRouter対応は追加要求として扱い、先行変更の公開完了と混同しない。
- OpenRouter対応の実装と事前検証: subagents 2232 pass / 7 skip、inline-skills 107 pass / 330 assertions、両方lint/typecheck成功（inline formatも成功）。親self-reviewでinlineのprovider:null既定化を修正し、subagentsの不要な型castを除去した。Pi SDK + fake HTTPの9ケースがPASS。独立レビューは指摘なしで完了し、レビュー後の23変更ファイルのhash一致も確認した。後続の明示承認により、subagents `95119ca`、inline-skills `9e2b286`をそれぞれ`feat/jev-routing`へcommit/push済み。dotfilesのcommit/push/archive・実API試験・本番切替は行っていない。詳細は上記OpenRouter計画の検証記録。

## 自動本文挿入・通知・コンパクション対応の再設計（2026-09-30）

- 現在のinline-skillsは`9e2b286`を導入済みで、Jevは有効。今回の改修は既存のOpenRouter対応とは別の設計・承認対象とする。
- Jev選択後にモデルへ標準readを指示する方式から、拡張が選択スキル本文を読み、応答前のコンテキストへ直接挿入する方式へ変更する。
  - 出典: 自動本文挿入の提案へのユーザー合意。旧Q18の自動read指示を置換する。手動ロードとPi標準のスキル一覧は維持する。
- 通常の候補・スコア・レイテンシ診断通知をやめ、実際のロード成功時だけ`inline-skills: loaded use-zellij by Jev`の形式で通知する。複数件は名前をカンマ区切りにする。警告は別扱い。
  - 出典: 通知を簡潔にしたいというユーザー要望と文面合意。ターン終了時にまとめる案を提示済み。本文の履歴表示方法など未確定の公開挙動は計画確定前に整理する。
- Jevへの送信内容・上限は変更しない。展開したスキル本文をJevへ再送しない。通常の会話本文に含まれる秘密情報の一般的な自動マスキングは追加しない。
  - 出典: ユーザーの「送信されるデータは特に修正不要」。
- `jev.excludedSkills`は空配列にする。ask-codex、commit-push、doc-updater、herdr、implement、planの固定除外を廃止し、運用して問題があれば見直す。
  - 出典: 「いったん全部有効にしておこう。実際に運用して、困ったら考える」。設定変更・JSON検証済みで、ユーザーがreload済み。旧Q7の固定除外方針を置換する。`disable-model-invocation`や各スキルの実行条件、操作の承認要件は変更しない。
- コンパクションで本文がコンテキストから落ちても、ロード済み記録が残って再選択を妨げる現状を改善する。
  - 出典: 現行の判定ロジック説明に対するユーザーの「これ改善したいね」。
  - 確認済み: `restoreLoadedSkillNames()`はactive branch全体から成功read記録・inline custom message・native skill展開を復元する。既存`test/session-lifecycle.test.ts`は、コンパクション後もロード済み扱いを維持して本文を再挿入しない挙動を仕様として検証している。単なるテスト不足ではなく仕様変更が必要。
  - Q24はAで決定（ユーザー「a」）: 本文が実効コンテキストから消えたスキルはJevの候補へ戻し、手動指定でも再ロードできるようにする。本文が残るものは重複ロードしない。過去の利用履歴は削除せず保持する。コンパクション後に以前の本文を一括で自動再挿入する方式は採用しない。
  - 今後の確認: 実効コンテキストと履歴上の利用記録の分離、手動/native/read/自動挿入の共通判定、再試行・resume・branch切替との整合。実装・新計画の保存はまだ行っていない。
- Q25はAで決定（ユーザー「a」）: Jevによる自動挿入は短い成功通知だけを表示する。本文はモデル用コンテキストとセッション履歴へ保存するが通常チャットには表示しない。手動ロードの既存表示は維持する。
- 設計の最終確認待ち: 自動本文挿入、成功通知のみの表示、本文消失後の必要時再ロード、標準スキル一覧・送信範囲・手動経路の維持をまとめて確認し、確認後に新しい実装計画を保存する。

## 対象外
- nicobailon/pi-subagents への置換。
- 前段調査だけを根拠に他の Jev 拡張を一括導入すること。

## 実装計画への引継ぎ記録
- 確認済みの既存優先順位: Agent の resolveAgentInvocationConfig は agent 定義 > 呼び出し指定。Workflow host の spawnAgent は呼び出し指定 > agent 定義。Jev は両方が未指定の項目だけを補い、この既存差は変更しない案。親への model/effort 指定指示は、自動選択を基本とする運用への調整を提案する。
- Agent / SubagentWorkflow / 再開での適用範囲。
- model と effort の候補、選択基準の具体的な表現・設定方法。
- 自動選択の除外リストの初期内容を既存スキルから整理する。
- 導入済み inline-skills の src/index.ts を確認済み。input で明示指定を解決し before_agent_start で挿入する。read の tool_result と inline-skill custom message から branch のロード済み状態を復元している。自動選択もこの管理へ統合する案。
- API キーの受け渡し・タイムアウト値・低信頼度の判定基準・観測方法。スキル連携側の障害時の挙動。
- スキル選択に送る直近会話の件数・文字数上限と、送信対象外の内容を取り除く実装方法。
- fork の作業場所は /Users/ryo.nakae/Dev/private/pi-inline-skills を提案。テストと段階的な切替手順は計画で具体化する。
- pi-subagents の AGENTS.md は commit 禁止、明示依頼のない push/tag/branch 作成禁止。実装工程でこれを守り、計画にも反映する。

### 設計確認時の提案記録（最終実装計画を優先）
- Q13 の初回提示時は未承認。その後ユーザーは両拡張のオン・オフ設定とMarkdown管理を追加要望し、最終構成と実装計画を承認した。
- model/effort 選択方式の提案: 有効な model × effort の組み合わせに内部候補 ID を付け、Jev の Choice の選択肢として渡す。自由文のモデル名・effort を生成させない。候補の用途説明は自然文、識別子・参考指標は構造化データとし、返答 ID をローカルの候補表へ引き戻す。
- 明示指定・agent 定義の固定値があれば候補をその値に限定する。両項目とも固定なら API を呼ばない。結果の候補 ID・値の妥当性と信頼度を検証し、不正・低信頼度なら合意済みのフォールバックへ戻す。
- 候補の能力・用途説明と参考ベンチマークは設定で管理する。Pi のモデル登録情報だけから能力・実タスクでの速度を推測しない。Jev の confidence は成功率の保証として扱わない。
- ユーザーの管理場所・方法に関する質問への提案（未承認）: dotfiles 正本の config/.pi/agent/subagents.json の jev セクションに candidates 配列を置く。各要素は model / effort の組み合わせと用途説明・任意の参考ベンチマークを持つ。~/.pi/agent/subagents.json から拡張が読む既存の配置を使う。
- settings.json の enabledModels は利用許可、jev.candidates は自動選択へ参加する組み合わせという別の役割とする。候補を enabledModels・利用可能モデル・対応 effort で検証し、候補 ID はコードで生成する。定義されていない組み合わせを Jev に自由生成させない。
- 初期候補の説明・比較データは既存の選定指示とベンチマーク表から整理して移す。数値には出典・測定条件を付け、実行時の料金や性能を保証する値とは扱わない。モデル能力説明・比較表をツール説明にも重複維持するのは避け、通常の自動選択では設定を正本にする。
- agent-tool-description.md との関係について追加提案（未承認）: 現在の「新規 Agent は原則 model と thinking を指定」の指示は Jev の未指定項目選択と競合するため、オン・オフに応じた案内へ置き換える。委譲判断・役割選択・タスクの書き方・並列化・親の検証・失敗原因の切り分けは Markdown 側に残す。
- 現在の src/index.ts の renderToolDescriptionTemplate は {{compactTypeList}} 等の動的展開に対応することを確認済み。この仕組みに {{modelSelectionGuide}} を追加する案。Jev オン時は通常省略・明示指定の扱い・フォールバックの短い案内、オフ時は設定を正本として生成する選定方針・候補・比較表と従来の明示指定指示を展開する。新規プレースホルダーであり現時点では未実装。
- 最新の管理構成案: 自然文の選定方針は config/.pi/agent/model-selection-guide.md を正本とし、Jev の判定指示と Jev オフ時の親向け説明で共用する。Jev オン時に親へ渡す短い任せ方・手動指定の案内は config/.pi/agent/model-selection-auto-guide.md で管理する。subagents.json は候補の model/effort と構造化された比較データを管理する。自然文の方針を JSON にも重複保存しない。
- {{modelSelectionGuide}} はオン時に auto-guide、オフ時に通常の guide を読み込んで展開する。必要な候補表は新規の {{modelCandidates}} プレースホルダーで設定から展開する案。コードの役割は読み込み・オンオフの切替・構造化データの整形・検証であり、ユーザー固有の説明文をハードコードしない。
- Markdown と比較データを移す際に、ベンチマークの出典・測定条件・誤差・適用限界を失わない。Jev オンでも手動選択が必要なら親が同じ guide と設定を参照できるよう説明する。
- オン・オフ切替時はモデル解決とツール説明を一致させる。既存の説明は登録時に生成されるため、設定反映のタイミング（再読込等）を計画で明示する。
- オン・オフ設定の既定値は要確定。提案は拡張の既定をオフ、今回の利用設定でオン。既存セッションのモデルやロード済みスキルを設定オフ時に巻き戻さず、以後の新しい判定を停止する。
- Jev の model/effort 選択は Agent と SubagentWorkflow の新規起動に適用する。既存セッションの再開では再選択しない。既存の明示指定・定義値の優先順位は各経路で維持する。
- 初期 model 候補は現在の enabledModels にある Luna / Terra / Sol / Astra の4モデル。effort は各モデルで対応する値に限定し、候補と判断基準は設定で管理する。片方が固定ならそれを制約として未指定項目だけを選ぶ。
- 親へのツール説明・運用指示は、通常 model/effort を省略して Jev に任せる内容に調整する。
- API キーは両拡張が TYPESAFE_API_KEY から読む。Safehouse への明示的な受け渡しを設定し、Git にキーを保存しない。
- 初期の Jev 呼び出し上限は全体5秒、自動リトライなし。モデル版は jev-1.13.0 に固定して再現性を確保する。
- スキル選択失敗時は警告して自動追加だけを見送り、明示ロードと本来の依頼は継続する。
- スキル選択の会話入力は今回の依頼を含む直近最大6メッセージ・合計12000文字を初期上限とする。1ターンの自動追加は最大3スキル、該当なしも許容する。上限と閾値は設定可能とし、日本語の代表ケースで検証する。具体的な判定方式と閾値は計画で根拠とともに提示する。
- 明示指定・ロード済みのスキル名も判断材料に含め、本文は送信しない。自動ロードは既存の branch 単位の履歴管理へ統合する。
- 選択結果・フォールバックの有無・待ち時間を確認可能にするが、タスク本文・会話・API キーを専用ログへ追加保存しない。
- subagent 内でスキル自動選択しないことは、識別方法を実装前に確認し、テストで保証する。
- Node の要件を満たす環境を検証の前提とし、実際の環境更新・リポジトリ公開・push・本番設定切替の手順と承認範囲は計画に明記する。設計確認は実装開始の承認とは分ける。

## 撤回・置換済み
- 旧Q3の「Jev不採用時は警告し、未指定値を通常継承して起動」は、実Jev検証後のユーザーの意図確認により「親がタスクに応じてmodel/effortを判断」に置換。現在のコードと計画には旧方式が残っているため、同一の挙動として扱わない。
- Agent/Workflow間のmodel/effort優先順位の差を維持する初期方針は、定義済み値を最優先とする今回の要件に合わせて見直す対象になった。
- Q5・初期実装計画のJev選択スキル本文の自動挿入は、Q18でメインモデルへの標準read指示に置換。入力transform/message_end置換や独自の複数本文折りたたみは、自動選択の方式として追わない。Q19で手動指定は従来の直接挿入を維持すると決定した。
- Q14で推奨したPi側の公開API追加案は採用しない。ユーザーが拡張内で完結するBを選択したため、Pi本体のfork・API追加は今回の対象外とする。
- modelSelectionGuide の案内文をコード側で定義し、自然文の選定方針を subagents.json に置く案は、ユーザーが Markdown で編集できる構成へ変更する。最新の管理構成案を優先し、以前の提案にある「設定から説明文を生成」は候補表など構造化データの整形に限定する。
- Q9 の当初推奨「今回の依頼文と候補スキルの名前・説明だけを送る」は、文脈依存の応答を解釈できないため撤回。上限付きの直近会話を含める方針に置換した。
