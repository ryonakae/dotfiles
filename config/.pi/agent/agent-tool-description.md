原則としてメインエージェントが直接作業する。サブエージェントは、並列化・モデル切替・文脈の独立に明確な目的がある場合、またはユーザーが委譲を明示した場合に使う。

## 委譲の判断と実行

次のいずれかに該当する場合だけ委譲を検討する。

- **並列化**: 独立したまとまった作業を渡し、その間にメインも別の作業を進められる。
- **速度・費用**: 範囲と報告形式を限定した調査などを、必要な品質を保ちつつ、メインより高速・低コストなモデル × thinkingで処理できる。
- **品質向上**: 難しい判断や重要なレビューを、そのタスクでメインより高い品質を見込めるモデル × thinkingに任せる。
- **文脈の独立**: メインの仮説に引きずられない評価や、別の前提での検討など、会話履歴を共有せず作業させる目的が明確。文脈の分離だけが目的なら同じモデルも候補にし、モデル固有の偏りを補う目的なら異なるモデルを検討する。
- **明示的な依頼**: ユーザーがサブエージェントへの委譲を求めている。

ユーザーの明示的な依頼がない場合は、期待する利益が起動・文脈共有・結果待ち・親による検証の負担を上回ることも条件とする。調査範囲が広いことや、担当可能なtypeが存在することだけでは起動しない。迷ったら直接作業する。

- 委譲の要否と目的 → typeの役割・ツール・権限 → モデル × thinkingの順に選ぶ。
- `prompt`に目的、必要な事実、対象範囲、変更可否、完了条件、報告形式を含める。新規エージェントは既定では会話履歴を持たない。文脈の独立が目的なら会話履歴を継承せず、メインの結論や仮説も必要以上に渡さない。
- 独立した作業だけを並列化する。編集ファイルだけでなく共有API・ビルド・生成物の依存も確認する。結果待ち以外に進める作業があるときだけバックグラウンドで起動する。モデル切替や文脈の独立に利益がある場合は、親が結果を待つ同期委譲も認める。
- バックグラウンド実行では完了通知を待つ。同期・非同期とも、親が差分・テスト・出典を検証する。

## 長時間コマンドの実行

- 終了まで時間がかかるビルド・テスト・コマンドは、メインが独立した作業を進められる場合、軽量モデル・低thinkingのサブエージェントへ `run_in_background: true` で委譲する。確定済みコマンドの実行だけならLuna lowを第一候補とし、会話履歴全体は継承せず必要な実行条件だけを渡す。
- メインが実行コマンド、作業ディレクトリ、必要な環境、タイムアウト、ログ保存先を指定する。子は通常の `bash` で終了まで待ち、終了コード・結果要約・ログパスを返す。タイムアウト・中断は成功扱いせず、独自の修正・再試行・再委譲は行わない。
- メインは通知待ちのポーリングや `sleep` を行わず、入力・生成物と競合しない作業を進める。完了通知後に終了状態と必要なログを確認し、起動だけで検証完了としない。
- 短いコマンドや、その結果なしには次へ進めない処理はメインで直接実行する。常駐プロセスやPi終了後も継続する必要がある処理を、この委譲で管理できるとはみなさない。

## 利用可能な種類

{{compactTypeList}}

## モデル × thinkingの選択

委譲すると決めてから、次の順に選ぶ。

1. **タスクを評価する。** 必要な判断の量（固定手順か、解釈・設計か）、依存の広さ（局所か、複数の状態・契約を追うか）、正否の検証しやすさ、失敗時の影響を確認する。ファイル数や依頼文の長さだけで難易度を決めない。
2. **モデル × thinkingを一体で比較する。** 下位モデルの高thinkingと上位モデルの低thinkingも同じ候補集合に入れる。モデルを先に決めたりtypeに固定したりせず、同一モデルや同じthinking同士に比較を限定しない。軽量作業ではLunaも候補に含め、上位モデルや高thinkingを自動的に選ばない。
3. **委譲内容とベンチマークの類似性を確認する。** スコアからタスク別の必要点数を導かない。
   - **実装・修正・検証まで任せる仕事**: Terminal-Benchを優先し、Intelligenceを補助にする。
   - **入力資料が揃った読解・抽出・統合**: AA-LCRを参照する。知識に基づく回答ではOmniscienceも参考にする。Terminal-Benchの低さだけで候補を除外しない。
   - **探索を伴う調査**: 必要な資料の発見、ツール操作、依存関係の追跡、仮説検証が必要ならAA-LCRだけで選ばない。探索経路の判断量と検証の難しさを評価し、ターミナル作業を伴う場合はTerminal-Benchも補助にする。
   - **コードレビュー**: 4指標とも見逃し・誤検出を直接測らない。局所的で指摘をテスト等で確認できる仕事では軽量な候補も検討する。複数の状態・契約を追う仕事や、指摘・見逃しを検証しにくい仕事では、その推論を担える能力を優先する。「重要なレビュー」というだけで上位モデル・高thinkingに固定しない。独立した再確認が目的なら同じモデルも候補にする。いずれも親が指摘の再現・検証を行う。
   - **共通**: 費用・時間とthinkingを変えたときの差を見る。高thinkingほど高得点になるとは限らない。小差だけで優劣を断定せず、ベンチマークの成功率を個別タスクの成功率や品質保証として扱わない。
4. **品質・時間・費用の釣り合う組み合わせを選ぶ。** ユーザーの優先事項に従い、指定がなければ次の順に判断する。
   - タスクの難しさ・検証可能性・失敗時の影響から、必要な品質を見込めるモデル × thinkingに候補を絞る。役割ごとの固定モデルや点数の閾値は設けない。
   - 残った候補間で、品質差を重視する根拠が弱い場合は費用・時間を比較する。起動・文脈共有・再試行・親の検証の負担も含める。
   - 品質の見込みに不確実性が大きく、失敗の影響も大きい場合は、費用・時間よりそのタスクに必要な能力を優先する。単にベンチマークが未整備という理由だけで最上位・最大thinkingに寄せない。
   - 常に最安から試す必要はない。ベンチマークの費用・速度はPiでの実測ではなく、異なる単位を任意の重みで合算しない。
5. **不十分な結果は原因を切り分ける。** 推論が浅ければthinking、意味の取り違えならモデルを再検討する。情報不足は依頼を補い、時間超過はまず範囲・依存関係・ツール待ちを確認する。認証・権限・ツール障害をモデル変更で解決しようとしない。

### 呼び出し時の指定

- 新規の`Agent`では原則`model`と`thinking`を指定し、省略は継承を意図した場合に限る。agent定義の固定値は呼び出し引数より優先される。
- 再開は既存セッションを継続し、model・thinkingの変更は反映されないため指定しない。切替が必要なら新規起動とし、文脈を失う負担も考慮する。
- `SubagentWorkflow`は別のツール仕様に従う。

モデルID:

- Luna: `openai/gpt-6-luna`
- Sol: `openai/gpt-6.1-sol`
- Astra: `openai/gpt-6-astra`

## 比較データ

[Artificial Analysis](https://artificialanalysis.ai/)（2026-10-01確認）。3モデルともlow / medium / high / xhigh / maxの4指標・費用を取得。時間はLuna mediumのみ未掲載。表はサイトの表示精度で記載し、未掲載値の補間や他世代からの流用はしない。起動ごとの再検索は不要。

- **Intelligence**: Intelligence Index v4.3.2。10評価の総合指標で、成功率ではない。
- **Terminal-Bench**: Terminal-Bench 4.0。ターミナル上の複雑な作業のpass@1。実装・修正・検証を任せる際の参考にする。
- **AA-LCR**: AA-LCR v1.1。長文資料の抽出・推論・統合の正答率。リポジトリ探索やコードの依存関係追跡を直接測るものではない。
- **Omniscience**: AA-Omniscience Index（−100〜100）。正答を加点、誤答を減点し、回答保留は減点しない。検索能力やレビューの誤検出率ではない。
- **USD/task**: Intelligence Indexの評価タスクあたり加重平均費用。Piの実作業費用やCodex契約の消費量ではない。
- **推定decode秒/task**: 比較ページの「Time per Task」。Intelligence Indexの各評価の出力トークン数と生成速度から算出した、タスクあたりの加重平均decode時間（秒）。低い方がよい。TTFT・ツール実行・その他のオーバーヘッドを含まず、Piでの実測完了時間ではない。「未掲載」は0秒ではなく、速度比較の根拠にしない。

4指標はすべて高い方がよい。個別3評価はIntelligenceの構成要素でもあるため、足し合わせて独自の総合点にしない。用途に近い内訳と費用・推定decode時間を参照する。主に英語・テキストでの評価であり、日本語、画面操作、コードレビュー、Piでの性能を直接保証しない。出力速度やdecode時間を実作業の完了時間に読み替えない。

| モデル | effort (thinking) | Intelligence | Terminal-Bench % | AA-LCR % | Omniscience | USD/task（参考） | 推定decode秒/task |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna | low | 22 | 0 | 74 | -9 | 0.0045 | 16.50 |
| Luna | medium | 30 | 3 | 78 | -5 | 0.02 | 未掲載 |
| Luna | high | 33 | 5 | 79 | -6 | 0.03 | 159.59 |
| Luna | xhigh | 35 | 8 | 80 | -2 | 0.04 | 209.61 |
| Luna | max | 38 | 13 | 83 | 1 | 0.07 | 396.30 |
| Sol | low | 42 | 31 | 84 | 38 | 0.13 | 69.95 |
| Sol | medium | 48 | 48 | 83 | 40 | 0.21 | 137.12 |
| Sol | high | 50 | 52 | 82 | 41 | 0.32 | 212.09 |
| Sol | xhigh | 51 | 54 | 80 | 41 | 0.39 | 287.49 |
| Sol | max | 52 | 56 | 83 | 42 | 0.72 | 592.53 |
| Astra | low | 46 | 42 | 80 | 41 | 0.82 | 101.93 |
| Astra | medium | 50 | 49 | 80 | 42 | 1.54 | 213.89 |
| Astra | high | 51 | 54 | 80 | 44 | 1.73 | 265.21 |
| Astra | xhigh | 52 | 60 | 80 | 43 | 2.31 | 359.75 |
| Astra | max | 53 | 59 | 81 | 43 | 3.26 | 527.79 |

出典: [評価方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking)。費用は各リリースページの「Cost / Per Intelligence Index Task」: [Luna](https://artificialanalysis.ai/models/releases/gpt-6-luna)、[Sol](https://artificialanalysis.ai/models/releases/gpt-6-1-sol)、[Astra](https://artificialanalysis.ai/models/releases/gpt-6-astra)。

4指標・推定decode時間のeffort別比較ページ:

| effort | Astra / Sol | Sol / Luna |
|---|---|---|
| low | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-astra-low-vs-gpt-6-1-sol-low) | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-1-sol-low-vs-gpt-6-luna-low) |
| medium | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-astra-medium-vs-gpt-6-1-sol-medium) | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-1-sol-medium-vs-gpt-6-luna-medium) |
| high | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-astra-high-vs-gpt-6-1-sol-high) | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-1-sol-high-vs-gpt-6-luna-high) |
| xhigh | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-astra-xhigh-vs-gpt-6-1-sol-xhigh) | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-1-sol-xhigh-vs-gpt-6-luna-xhigh) |
| max | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-astra-vs-gpt-6-1-sol) | [比較](https://artificialanalysis.ai/models/comparisons/gpt-6-1-sol-vs-gpt-6-luna) |
