# Inline Skills 自動本文挿入・コンパクション対応 Implementation Plan

実装・検証完了後、個別承認により`6b601ae`をcommit/push・導入した。導入済みコードでも自動ロード・reload・コンパクションの合成TUI検証に成功。その後masterへ統合し、README更新後の`9491b98`を導入、ユーザーがreload完了を確認した。以下のcommit/push・本番更新未実施という記述は各段階の記録として残す。

## Requirements

Jevが選んだスキルをモデルによる追加readなしで利用可能にし、通知を簡潔にする。あわせて、コンパクションで本文が消えたスキルがロード済み扱いのまま再選択されない問題を改善する。

- 自動選択したSKILL.mdを拡張が読み、対象のモデル要求へ応答前に挿入する。自動本文はセッション履歴に保存するが通常チャットには表示しない。
- 自動ロード成功時だけ`inline-skills: loaded use-zellij by Jev`を通知する。複数件は`inline-skills: loaded use-zellij, worktrunk by Jev`の形式でまとめる。候補、スコア、レイテンシ、該当なしの通常診断通知は出さない。失敗警告は維持する。
- 過去の利用履歴と、現在のコンテキストに本文が残るスキルを分離する。本文が消えたものはJevの候補へ戻し、手動指定でも再ロードできる。残っている本文は重複ロードしない。以前のスキルをコンパクション後に一括復元しない。
- 手動`/skill名`の直接挿入と表示、Pi標準`/skill:名前`の展開、標準スキル一覧、補完を維持する。
- 自動選択はメインセッション限定。off、子セッション、不明なchild identityでは自動選択しない。明示指定・本文が残るスキルの除外、スコア順・閾値・最大件数、認証・中断の契約を維持する。
- Jevへの送信範囲と制限を維持する。現在入力を含むuser/assistantテキスト最大6件・12000文字、シリアライズ後65536バイト、HTTP timeout 5000ms、minRelevance 0.85、maxSkills 3という運用設定は変更しない。新たな自動本文もcustom messageとしてJevへの送信対象から除外する。一般的な秘密情報の自動マスキングは追加しない。
- ユーザーの明示依頼により、dotfilesの`jev.excludedSkills`はすでに`[]`へ変更・reload済み。この設定を戻さない。設定可能な除外機能と`disable-model-invocation`は維持する。スキルのロードは実行条件や操作の承認要件を解除しない。

参照: [既存Dig Log](../../dig/2026-09-28-pi-jev-routing.md)の「自動本文挿入・通知・コンパクション対応の再設計」。Q24=A（必要時だけ再ロード）、Q25=A（自動本文は非表示）、その後の全体確認へのユーザー「ok」で計画作成を承認。旧Q18の自動read指示、旧Q7の運用上の固定除外は最新合意で置換する。Dig Log末尾の最終確認待ち表記は本計画で解消する。

## Scope and baseline

- 実装対象: `/Users/ryo.nakae/Dev/private/pi-inline-skills`、`feat/jev-routing`、調査時HEAD `9e2b286`。調査時のworktreeはclean。Pi 0.87.1の公開SDKと既存Bunテストを使う。
- 本計画はdotfilesに保存する。dotfilesの既存変更、pi-subagents、MCP adapter、認証・Safehouse設定は変更しない。
- Pi内部API・表示のpatch、擬似tool call/result、入力への相関ID追加、新しい依存・設定スイッチは導入しない。既存の補完処理をついでに再設計しない。
- 実装開始、commit/push、導入済みパッケージ更新、npm公開、実API試験はこの計画作成の承認に含まれない。実装の承認後も公開・本番切替は別途明示承認を得る。

## Implementation Decisions

### コンテキスト内のロード状態

確認済みの現状:

- `src/loaded-skills.ts::restoreLoadedSkillNames()`はactive branch全体から、成功read記録・inline custom message・native展開を復元する。`src/index.ts`はその集合を手動ロードとJev候補の除外に使う。
- 公開`ctx.sessionManager.buildSessionProjection()`はコンパクションと`context_edit`を適用したメッセージと、それぞれの`sourceEntry`を提供する。`sourceEntry`は元の履歴であり、本文の有無は投影後の`messages`で確かめる必要がある。
- 既存`test/session-lifecycle.test.ts`には、コンパクション後に本文を再挿入しない旧仕様のテストがある。これは新仕様へ置換する。

採用方針:

- 履歴上のロード記録は削除・移行せず保持する。`/loaded-skills`は互換性のため従来どおりactive branchの利用履歴一覧とし、READMEで現在の本文保持とは異なることを明記する。
- 重複抑止とJevの`loadedSkills`には、投影後の本文に基づく集合を使う。本文のない記録、要約内のスキル名、custom messageのdetailsだけでは本文ありと認定しない。
- 手動・自動inline messageとnative展開は、由来と投影後のskill blockを対応させる。成功readは残存するtoolResultと実際のread呼び出しをtoolCallIdで対応させる。元のread引数を確認するために履歴を参照しても、結果本文が投影から消えていればロード済みにしない。
- 既存の`loaded-skill`記録はtoolCallIdを持たないため、過去の実tool call/resultから判定できる経路を残す。新しい記録に関連IDを追加する場合も既存履歴を必須migrationにしない。パス照合は既存のsymlink対応を利用し、失敗readは除外する。部分readや結果の切り詰めを完全読込へ格上げする新しい保証は追加しない。
- 実行中のrequest-local本文と保存済み本文を区別する。`context`時点では投影に加え、その要求に実際に渡す本文を考慮する。保存前だからといって同じ本文を重複挿入しない。
- 状態は初期化・reload時だけでなく各ロード判定時に再計算する。session/branch切替、コンパクション、本文を落とすcontext editに追従する。後続の任意拡張やproviderがさらに変換した最終内容まで追跡する機構は作らない。

### 自動挿入と履歴・通知

- `src/index.ts`の実消費user batch単位のJev選定を維持し、選択後のread指示を本文構築へ置き換える。既存`buildSkillInjection()`とskill block形式、相対参照の案内を使う。
- 自動本文は`inline-skill` custom message、`display: false`で保存し、自動由来をdetailsで識別できるようにする。手動messageは従来の表示を維持する。ユーザー本文に追加せず、provider変換後のroleからJev送信対象を再構築しない。
- `context`でモデル要求へ本文を加え、`pi.sendMessage(..., { triggerTurn: false })`で同じ本文の保存を予約する。Pi 0.87.1ではstreaming中の予約はターン終了時、tool call/resultの組が保存された後に反映される。
- 読み込み、要求への挿入、保存予約、保存確認を別の状態として扱う。手動と自動で同じbatch keyを使って一方の保存を抑止しない。retryではJev判定と構築済み本文を再利用し、保存・通知は重複させない。途中で本文がコンパクションされた場合も、保存済みという事実だけで再提供を永久に抑止しない。
- 成功通知は当該自動messageの保存を公開イベントで確認できる時点に出す。同時に自動挿入した成功分の名前を一つの通知にまとめる。resume/reloadで過去の通知を再発行しない。選択だけ、読み込み失敗だけ、無効化された遅延結果では成功通知しない。
  - 実装確認: Piの遅延custom message追加は拡張の`message_start`へ再配送されない。保存はターン終了時、成功通知は公開`agent_settled`で対応する保存件数の増加を確認して発行する。実TUIでも保存と1回の通知を確認した。
- 一部のファイルだけ読めなければ、そのスキルを警告し、成功分だけ挿入・保存・通知する。未読分はロード済みにしない。同じ失敗を同一batchの各contextで繰り返し通知しない。次の依頼や明示ロードで再試行できる。
- Jev/auth待機後のsignal・generation・実消費batch検査を維持し、本文挿入と保存予約の直前にも有効性を確認する。中断前に実際に挿入・保存対象となった本文は既存手動経路同様に当該履歴へ残せるが、遅れて到着した選択結果を別入力へ適用しない。モデルが応答したことやスキルを遵守したことを成功通知の意味に含めない。

## Tasks

実装開始記録: 計画提示後のユーザー「ok」で実装を承認。review baseは`9e2b28684c4e67a10fa30dea0f499b579153724d`。開始時の対象repoはstaged/unstaged変更なし、upstreamとの差分0/0。commit/push・本番更新は計画の対象外のまま。workerがrepo内の実装とSDKテスト、親が実TUI検証と独立レビューを担当する。

- [x] **コンテキストに基づくロード判定**: `src/loaded-skills.ts`、必要に応じて`src/read-tracking.ts`と`src/index.ts`の判定呼び出しを変更する。
  - 履歴一覧と重複抑止の集合を分離し、manual/native/readの残存本文で復元する。旧履歴と現在の履歴の両方を扱う。
  - `test/loaded-skills.test.ts`、`test/session-lifecycle.test.ts`、必要なread/手動テストで新契約を先に失敗させる。コンパクション後に本文がないのに再ロードできない旧仕様のテストは置換する。
- [x] **自動本文挿入・非表示保存・成功通知**: `src/index.ts`と`test/automatic-context.test.ts`を中心に、read指示を自動本文へ変更する。
  - 既存のbatch・retry・非同期無効化処理を活用し、手動との共存、成功分のみの保存と通知を実現する。旧read指示に依存したテストは新しい外部挙動へ置換する。
  - `test/harness.ts`は必要な観測だけ追加する。既存harnessのcustom message観測は`display`を見ずに収集するため、履歴にあることと画面に表示されることを混同しない。
- [x] **回帰検証と利用説明**: 関係するqueued、preflight、expansion、lifecycleテストを更新し、`README.md`と`CHANGELOG.md`を新挙動へ合わせる。
  - READMEの自動read説明、診断通知、ロード状態・コンパクション、非表示保存、再ロードと履歴一覧の意味を更新する。ユーザーの除外なし運用は明示的な`excludedSkills: []`で説明できるようにし、設定省略時のパッケージ既定値までは変更しない。
  - 公開forkのドキュメントは英語とする。由来・MITライセンスは保持する。

## Final Validation

既存Bun/実Pi SDK+faux providerでTDDを行う。実APIキーを渡さず、専用temporary HOME/agent directoryと合成資格情報、mock HTTPを使う。Node >=22.19とBunを使い、global Node設定は変更しない。

- [x] **本文と通知**: 通常入力の最初のモデル要求に選択本文が各1回入り、モデルによるreadなしで利用できる。複数件の順序、非表示の永続message、正確な成功通知1件を確認する。該当なしは無通知、一部/全部のread失敗は成功分のみ通知・保存する。
- [x] **コンパクション**: 手動inline・自動inline・native・成功readの各経路で、本文が消えれば再選択/手動再ロード可能、残れば重複なしとなる。要約内の名前や古いロード記録だけでは抑止されない。成功readの結果のみ残る境界とcontext editによる本文除去も確認する。`/loaded-skills`の過去履歴は保持される。
- [x] **retryと入力対応**: 既存のqueued/all-at-once、同文の別入力、native/template展開、preflight失敗、queue clear、provider error/retry、継続要求、途中コンパクションの該当ケースを更新する。判定の無用な再通信、本文消失、手動/自動の保存競合、別入力への本文漏れ、二重通知がないことを確認する。
- [x] **寿命と復元**: auth/Jev待機中のabort・batch変更・session/branch変更では遅延結果を破棄する。挿入後のerror/abortは履歴と整合し、reload/resume/fork/newSession後に対象ブランチの残存本文から復元される。旧形式のread記録を含むセッションも確認する。
- [x] **通信境界**: 両provider、off、child/unsupported identity、maxSkills=0、候補なしの既存テストを維持する。後続依頼・retry・reload・コンパクションを経ても自動本文のsentinelやcustom messageがJev payloadへ混入しない。現在入力込みの既存上限テストを保持する。明示的な空のexcludedSkillsが有効で、disable-model-invocationは引き続き除外される。
- [x] **全体チェック**: 対象repoで`bun test`、`bun run format:check`、`bun run lint`、`bun run typecheck`を実行し成功する。変更テストのred/green結果と最終結果を本計画に記録する。同じ変更に対する全体チェックを理由なく繰り返さない。
  - 初回worker実行・親ログ確認: 116 pass / 0 fail / 383 assertions、format成功、lint 0 warnings / 0 errors、typecheck成功。`/tmp/pi-inline-auto-implementation/final-*.log`。段階的なred/greenログも同ディレクトリに保存。
  - correction 1後に親が再実行: 118 pass / 0 fail / 403 assertions、format/lint/typecheck/diff check成功。`/tmp/pi-inline-auto-implementation/correction-{bun-test,format-check,lint,typecheck}.log`。
- [x] **TUI一度きりの確認**: 実サービスに接続しないfixtureでtool-call-markersを有効にし、自動ロードの短い通知だけが出ること、手動ロードの折りたたみ/展開と隣接ツール表示が壊れないことを通常幅・狭幅で確認する。resumeで自動本文が露出せず成功通知を再発行しないことも確認する。SDKのdisplayフラグ確認だけをTUI検証成功と扱わない。
  - 準備済み: `/tmp/pi-inline-auto-tui-fixture.ts`、`/tmp/pi-inline-auto-tui-check.py`。CLIを独立HOME・合成provider・mock HTTP・PTYで起動する。旧導入版に対する手動ケースはPASS（`/tmp/pi-inline-auto-tui-v0iz0o3k/`）、自動ケースは旧診断通知を検出して期待どおりFAIL（`/tmp/pi-inline-auto-tui-baseline.log`）。これは検証器の確認であり、変更後の受入完了ではない。
  - 変更後の7ケースPASS: auto（`/tmp/pi-inline-auto-tui-54nb1pdg/`、reload・手動compact・再選択も含む）、mixed（`…-r9vhj8ym/`）、normal（`…-zk0v29gq/`）、queued（`…-c9itsfpv/`）、native（`…-ykx256rb/`）、resume（normalと同じroot）、resume-auto（autoと同じroot）。80/30列、Ctrl+O、隣接する通常readのマーカー、モデル要求内の本文各1回、Jev payload非漏洩、成功通知、履歴保存、再開時の非表示と無通知を確認。
  - 検証器の修正: 自動messageは拡張のmessage_startでは観測できないため、保存確認を`agent_settled`のbranchへ変更した。短いfixtureで手動compactを実行するため`keepRecentTokens: 1`を設定した。いずれも製品コードの変更ではない。
- [x] **独立レビュー**: 並行入力・永続化・コンパクション・送信境界を重点として変更差分を読み取り専用でレビューする。親が指摘と修正差分・検証結果を確認する。修正後にも指摘が残る、新たな重大指摘が出る、または設計変更が必要になった場合は反復を続けずユーザーへ報告する。

### 独立レビューとcorrection 1

- 初回reviewer `a17db323-9f48-4b7`: blocking/high 1件、medium/low 2件。初回差分は11ファイル。commitなしのためレビュー対象はbaseからworking treeまでの差分。
- 採用したhigh: 旧セッションで成功read結果だけ残り、呼び出しとIDのない旧ロード記録が投影外になると、本文が残っていても未ロードと判定する。計画にあるactive branchの元read呼び出し参照を追加して修正した。投影内の未改変成功結果が存在することは引き続き必須とする。
- TDD: 旧形式履歴をSDKで構築し、結果を先頭としてcompactすると本文が2回入るredを確認（`correction-legacy-red.log`）。branch内の呼び出し照合を追加後、本文1回・再挿入なし、結果除去後は必要時再ロードとなるgreenを確認（`correction-legacy-green.log`）。
- 受入検証不足の指摘に対応: queuedケースを初回alpha自動→queuedでplan手動＋beta自動に変更し、初回betaなし・queuedで各本文1回・1 settlementで自動通知2件各1回をsteer/followUpで確認。挿入後abort時に本文が保存されて通知1回、その後も重複しないSDKテストを追加。製品コードの追加修正は不要で、28件PASS（`correction-acceptance.log`）。
- 残すmedium/low: 他拡張がtool_callでreadパスを変更した場合、投影の元引数の照合失敗から正しいID付き記録へフォールバックせず、重複ロードする可能性。重要度に従い今回のcorrectionでは変更しない。
- correction 1のscoped re-reviewは同じreviewerで完了。high解消、新たなblocking/high・decision requiredなし、マージ可能の判定。限定SDKテスト42 pass / 193 assertionsと合成復元確認も成功。残る指摘は上記medium/low 1件のみ。TUIの表示・自動挿入経路はcorrectionで変更していないため、通過済み7ケースの結果を再利用する。
- 最終gate: base `9e2b28684c4e67a10fa30dea0f499b579153724d`からの11ファイルの未コミット差分をレビュー。検証・レビュー対象のSHA-256は`/tmp/pi-inline-auto-implementation/correction-source.sha256`。全118テスト、format/lint/typecheck、実TUI、独立再レビューを通過した。承認範囲に従いcommit/push・本番更新・実API試験は未実施。dotfilesの既存の無関係な変更は保持。

各タスクは対応する検証が成功してから完了にする。実装中の軽微な差分と検証結果は該当箇所へ反映し、要件、対象外、公開契約の変更はユーザーへ確認する。最終確認では有効な検証結果を再利用し、計画と実際の変更が一致することを確認する。必要な検証と実装側の必須レビューが通ったら、計画を同名のまま`docs/plans/archived/`へ移す。
