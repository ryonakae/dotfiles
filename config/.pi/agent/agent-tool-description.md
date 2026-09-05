## 委譲

- 既知ファイルの読取や確定済みの操作は親が直接行う。独立した並列作業、広いread-only調査、独立レビューを委譲し、親が完了を待つだけの変更作業は委譲しない。
- 委譲の要否 → typeの役割・ツール・権限 → modelとthinkingの順に選ぶ。typeや新モデルの存在を委譲の理由にせず、モデルをtypeに固定しない。
- `prompt`に目的、既知の事実、対象範囲、変更可否、完了条件、報告形式を含める。新規エージェントは既定では会話履歴を持たない。
- 独立した作業だけを並列化する。結果待ち以外に進める作業があるときだけバックグラウンドで起動する。完了通知を待ち、親が差分・テスト・出典を検証する。

利用可能な種類:
{{compactTypeList}}

## モデル選択

新規の`Agent`呼び出しでは原則`model`と`thinking`を指定する。全モデル・思考レベルを比較し、再試行と親の検証を含む負担を考慮する。同種タスクのPi実測を優先し、下表は初期判断に使う。

- Luna: `openai-codex/gpt-5.6-luna`
- Terra: `openai-codex/gpt-5.6-terra`
- Sol: `openai-codex/gpt-5.6-sol`
- Astra: `openai-codex/gpt-6-astra`

### 条件別の早見表

候補の順序は順位ではなく、表外の構成も選べる。タスクへの適性と推奨thinkingは運用上の仮説であり、その組み合わせの実測保証ではない。

| 委譲する作業の条件 | 比較する候補 | 判断の手がかり |
|---|---|---|
| 抽出・分類を多数処理し、正解を機械的に確認できる | Luna low/medium、Terra low | 費用を重視。解釈が必要ならlowを避け、誤答の再処理も含めて選ぶ |
| 局所実装で仕様・テストが揃う | Luna high、Terra medium、Sol low | AAではLunaは低コスト、Terra/Solは短時間。複雑な状態変更なら次の行も比較 |
| 長い工程・状態追跡を伴う実装 | Astra low/medium、Sol high/max、Terra max | DeepSWE公式でAstra lowはLuna max、mediumはSol maxと近い点数で短時間・少ステップ。高thinkingを旧モデルだけに割り当てない |
| 広い原因調査・高影響レビューで、正解の検証も難しい | Sol high、Astra medium/high/max | 品質を優先。AAでAstra maxはRepo理解・ターン数、Sol highは時間で有利。Astraの他effortのRepo理解は未確認 |
| CLI中心で待ち時間を抑えたい | Sol low/medium、Terra medium、Astra low | AAのTerminalと実行時間を比較。Astra lowは時間未確認なので、最速扱いせず試行候補にする |
| 画面操作を伴うQA | Astra、Sol | 画像入力・操作ツールが使えるtypeを選ぶ。OSWorldをモデル候補の根拠にし、thinkingは操作の複雑さで決める |

### 比較と再試行

- **点数**: 実装はDeepSWE、探索はRepo理解、CLIはTerminal、複合タスクは総合点を重視する。点数を個別タスクの成功確率とみなさない。高影響・検証困難なら品質を優先する。
- **速度・コスト**: 必要な品質を見込める候補から、待ち時間重視なら実行時間、大量処理なら費用を重視する。指定がなければ品質 → 時間 → コストの順で比較するが、小差で順位を断定しない。API費用はCodexサブスクリプションの請求額・残量ではない。
- **ステップ数**: 往復の負担を見る補助指標。同等品質なら少ない構成を検討するが、早期失敗でも減り、少なくても1ターンの推論が長ければ遅い。異なる単位の指標を任意の重みで合算しない。
- **thinking**: 手順が明確ならlow、通常の複数ステップはmedium、深い追跡・境界条件はhigh、難しい仮説比較はxhighを出発点にする。maxは改善の根拠と時間・費用の許容がある場合だけ検討する。モデル変更に連動して上げず、対応レベルを確認する。AAのnoneをPiのoffに機械的に対応付けない。
- **不確実性**: 未測定はゼロ点や劣位ではない。他の評価から適性を見込めれば初回から試す。推論が浅ければthinking、意味の取り違えなら全モデルを再比較する。順番に全モデルを試す必要はない。
- **失敗**: 情報不足は仕様・再現手順を補い、認証・権限・ツール障害はモデルで解決しようとしない。誤った結果は採用せず、反証を次の依頼に含める。時間超過はまず探索範囲・出力を絞る。

## 比較データ

2026年9月公開評価。ハーネス・effort・料金条件を揃えて読み、Piの性能やCodex固有機能の利用を保証しない。起動ごとの再検索は不要。

### Artificial Analysis Coding Agent Index

[データ](https://artificialanalysis.ai/agents/coding-agents)・[評価方法](https://artificialanalysis.ai/methodology/coding-agents-benchmarking/)。CodexでDeepSWE、SWE-Atlas-QnA、Terminal-Bench v2.1のpass@1（各タスク3試行）を均等合成。効率指標は試行をプールした平均。

- 総合は0〜100、個別評価は%。Repo理解はSWE-Atlas-QnAで、レビューのバグ検出率ではない。
- 分は`mean.agentWallTimeSec / 60`（推論・ツール実行・応答待ち込み）、USDは`mean.costUsd`（キャッシュ反映のAPI費用）、ステップは`mean.steps`（Average Turns per Task。ツール呼び出し数や内部推論量とは別）。
- Astra low〜xhighの費用のみ[記事の図表](https://cdn.sanity.io/images/6vfeftx9/articles/5030dcb45684d0ac4ce33e799be92d7481aac40b-4653x4089.png)の表示値。`—`は数値未確認で、図の座標から補完しない。Astra maxはCodex 0.151.0、GPT-5.6は0.139.0〜0.147.0を含む。

| 構成 | 総合 | DeepSWE | Repo理解 | Terminal v2.1 | 分/タスク | USD/タスク | ステップ/タスク |
|---|---:|---:|---:|---:|---:|---:|---:|
| Luna (none) | 19.1 | 6.5 | 17.5 | 33.3 | 2.2 | 0.069 | 54.3 |
| Luna (low) | 25.1 | 10.3 | 15.1 | 49.8 | 1.7 | 0.039 | 34.3 |
| Luna (medium) | 42.0 | 36.6 | 27.2 | 62.2 | 3.2 | 0.088 | 57.1 |
| Luna (high) | 51.7 | 53.4 | 29.0 | 72.7 | 5.7 | 0.180 | 83.8 |
| Luna (xhigh) | 53.0 | 56.6 | 31.5 | 70.8 | 6.9 | 0.236 | 96.2 |
| Luna (max) | 57.2 | 63.4 | 32.8 | 75.3 | 8.0 | 0.288 | 114.6 |
| Terra (none) | 23.1 | 13.3 | 18.5 | 37.5 | 1.5 | 0.293 | 33.8 |
| Terra (low) | 38.6 | 29.8 | 22.8 | 63.3 | 2.6 | 0.385 | 37.8 |
| Terra (medium) | 48.0 | 45.7 | 28.8 | 69.7 | 4.0 | 0.670 | 51.0 |
| Terra (high) | 54.6 | 60.5 | 31.2 | 72.3 | 6.0 | 1.141 | 67.1 |
| Terra (xhigh) | 56.0 | 58.4 | 32.5 | 77.2 | 6.7 | 1.359 | 75.0 |
| Terra (max) | 60.4 | 67.0 | 36.0 | 78.3 | 8.2 | 1.930 | 95.8 |
| Sol (none) | 43.4 | 35.4 | 34.4 | 60.3 | 3.3 | 1.087 | 55.1 |
| Sol (low) | 55.2 | 53.4 | 34.4 | 77.9 | 3.5 | 1.292 | 53.9 |
| Sol (medium) | 61.6 | 64.0 | 40.3 | 80.5 | 5.0 | 2.193 | 71.4 |
| Sol (high) | 64.1 | 64.9 | 45.4 | 82.0 | 6.2 | 3.000 | 84.7 |
| Sol (xhigh) | 63.3 | 67.0 | 43.3 | 79.8 | 7.3 | 3.737 | 93.9 |
| Sol (max) | 65.1 | 68.7 | 43.3 | 83.1 | 10.2 | 4.995 | 112.3 |
| Astra (low) | — | — | — | — | — | 1.41 | — |
| Astra (medium) | — | — | — | — | — | 2.19 | — |
| Astra (high) | — | — | — | — | — | 2.89 | — |
| Astra (xhigh) | — | — | — | — | — | 3.27 | — |
| Astra (max) | 67.0 | 67.0 | 50.8 | 83.1 | 26.8 | 4.717 | 29.2 |

[AA記事](https://artificialanalysis.ai/articles/benchmarking-gpt-6-astra)の図ではAstra medium/highはSol max付近、xhigh/maxはそれ以上の総合点に位置する。Astra maxはSol maxより低コスト・少ターンでも約2.6倍遅く、時間とステップ数は代用できない。

### DeepSWE公式

[配布JSON](https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json)、2026-09-03生成。mini-swe-agentで113タスクを4周。採点対象試行のpass@1と平均効率、±は周回間の95%信頼区間の半幅。コンテキスト超過・タイムアウトは失敗、provider/verifier/networkエラーは除外。

USDは原典料金のまま。Astraは発売前想定（100万単位当たり入力$12、キャッシュ書込$15・読取$1.20、出力$50、compute units $2）で、他モデルも料金基準の統一は未確認。費用は同モデル内のeffort比較に使い、モデル間はAAを優先する。AAとこの表の点数・時間・費用・ステップを混ぜて比較しない。

| 構成 | DeepSWE % ±pp | 分/タスク | USD/タスク（原典料金） | ステップ/タスク |
|---|---:|---:|---:|---:|
| Luna (low) | 1.5 ±0.8 | 1.3 | 0.072 | 12.5 |
| Luna (medium) | 11.3 ±0.8 | 3.0 | 0.216 | 23.7 |
| Luna (high) | 44.2 ±2.9 | 7.9 | 0.778 | 49.0 |
| Luna (xhigh) | 56.9 ±2.2 | 12.2 | 1.536 | 71.1 |
| Luna (max) | 67.2 ±4.0 | 18.7 | 3.028 | 101.7 |
| Terra (low) | 24.1 ±0.8 | 2.9 | 0.428 | 21.5 |
| Terra (medium) | 35.1 ±3.4 | 3.8 | 0.583 | 25.1 |
| Terra (high) | 53.8 ±4.3 | 6.1 | 1.134 | 33.5 |
| Terra (xhigh) | 60.2 ±2.1 | 9.7 | 2.127 | 43.1 |
| Terra (max) | 69.6 ±2.6 | 16.9 | 4.946 | 75.9 |
| Sol (low) | 45.4 ±2.4 | 4.4 | 1.074 | 23.4 |
| Sol (medium) | 61.1 ±1.6 | 7.1 | 1.862 | 30.9 |
| Sol (high) | 69.4 ±1.4 | 9.9 | 3.470 | 36.9 |
| Sol (xhigh) | 70.7 ±0.8 | 13.3 | 4.704 | 44.0 |
| Sol (max) | 72.7 ±2.8 | 18.8 | 8.386 | 61.3 |
| Astra (low) | 67.0 ±1.3 | 10.2 | 2.189 | 19.5 |
| Astra (medium) | 72.8 ±2.6 | 14.7 | 4.380 | 26.0 |
| Astra (high) | 73.2 ±3.4 | 17.3 | 5.724 | 27.4 |
| Astra (xhigh) | 74.1 ±2.9 | 18.9 | 6.524 | 28.8 |
| Astra (max) | 73.2 ±0.8 | 33.0 | 12.369 | 28.5 |

信頼区間の重なる小差を確定順位にしない。Astra mediumからhigh/xhighの改善は小さく、maxはhighと同点で約1.9倍の時間・約2.2倍の費用。高thinkingを自動的に優先しない。

### 補助評価

- [OpenAI公開評価](https://openai.com/index/gpt-6-astra/)（Astra / Sol）: Terminal-Bench 4.0は57.9% / 37.3%、FrontierCode 1.1 Mainは53.3% / 47.5%、Extendedは64.5% / 60.6%、OSWorld 2.0は72.6% / 65.7%。各モデルのeffort別最高値であり、low/medium/highの実測として扱わない。
- [AAのAstra分析](https://artificialanalysis.ai/articles/benchmarking-gpt-6-astra): Intelligence Index v4.1.1は両者61。AA-Briefcaseの分析品質は改善する一方、GDPval-AA v2、SciCode、AA-LCRは低下しており、全分野でAstraが優位とは言えない。

## 適用範囲

この文書は新規`Agent`呼び出し用。agent定義のmodel/thinking固定値は呼び出し引数より優先される。省略は継承を意図した場合に限る。再開は既存セッションを継続し、`SubagentWorkflow`は別のツール仕様に従う。

全文をAgentの説明として登録する。編集は自動反映されないため、実行中のサブエージェントがいない状態で`/reload`するかPiを再起動する。
