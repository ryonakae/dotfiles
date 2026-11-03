# モデル × 思考レベルの比較データ

[Artificial Analysis](https://artificialanalysis.ai/) の値（2026-10-31 確認。AutomationBench・AA-Briefcase は 2026-11-03 確認）。起動ごとの再検索は不要。Gemini 3.8 Flash の値は Google のモデルのもので、Antigravity 経由の実測ではない。

内容: 指標、帯ごとの目安、ぶれ幅、比較表、データの更新（値を更新するときだけ読む）。

## 指標

- **Intelligence**: Intelligence Index v5.0。9 評価の総合指標で、成功率ではない。
- **Terminal-Bench**: Terminal-Bench 4.0。ターミナル上の複雑な作業の成功率。
- **FrontierCode**: FrontierCode 2.0。実在するリポジトリの変更をテストと評価基準で採点した平均スコア。必須条件を満たさない試行は 0 点、それ以外は部分点を含む。タスク成功率ではない。
- **GDP.pdf**: 長い業務文書を読んで回答する評価。すべての評価基準を満たした試行の割合（All-pass）。検索・ツールは使わず、対応モデルにはページ画像も渡す。リポジトリ探索やコードの依存関係追跡を直接測るものではない。
- **AutomationBench**: AutomationBench-AA。Gmail・Slack・Jira などを模した複数の SaaS を REST API のツール呼び出しで操作する業務フローの評価。最終状態をプログラムで検査し、達成した目標の割合を採点する。禁止事項に違反した試行は 0 点。
- **AA-Briefcase**: 数千の資料を入力にした、複数週にわたる知識作業プロジェクトの評価。成果物を評価基準と一対比較で採点した Elo で、成功率ではない。
- **Omniscience**: AA-Omniscience v1.1 Net Score（−100〜100）。正答を加点、誤答を減点し、回答保留は減点しない。検索能力ではない。
- **USD/task**: Intelligence Index の評価タスクあたり加重平均費用。T3 での実作業費用やサブスクリプションの消費量ではない。
- **秒/task**: 比較ページの「Time per Task」。評価タスクあたりの加重平均 decode 時間で、初回トークン待ち・その他の処理時間は含まない。低い方がよい。T3 での実測完了時間ではない。「未掲載」は 0 秒ではなく、速度比較の根拠にしない。

7 指標はすべて高い方がよい。主に英語・テキストの評価で、一部は画像を含む。Claude 系の行はサイト上の「(effort, Default Fallback)」バリアントの値である（Haiku 5.5 は Fallback 表記なし）。

## 帯ごとの目安

[delegation.md の選定手順](delegation.md#共通の選定手順) の帯ごとに、下限を満たす組み合わせを費用の安い順に並べた。括弧内は指標の値・USD/task・秒/task。

- **上位帯**: 最高値からぶれ幅を引いた値以上。最良の組み合わせと区別できない。
- **中位帯**: 最高値の半分以上。上位帯と下位帯の下限の中間に置いた慣習的な区切りである。
- **下位帯**: ぶれ幅を超える。まったく機能しない組み合わせと区別できる。

| 帯 | Terminal-Bench（最高 64） | FrontierCode（最高 46） | GDP.pdf（最高 32） |
|---|---|---|---|
| 上位 | 52 以上: Sol high（52、0.59、375）、Sol xhigh（54、0.76、426）、Terra max（56、0.96、610） | 37 以上: Terra high（37、0.26、180）、Terra xhigh（37、0.40、283）、Sol high（37、0.59、375） | 22 以上: Terra low（26、0.07、48）、Sol low（27、0.16、113）、Terra medium（28、0.17、119） |
| 中位 | 32 以上: Terra medium（32、0.17、119）、Terra high（42、0.26、180）、Sol medium（48、0.36、264） | 23 以上: Terra low（24、0.07、48）、Haiku high（23、0.16、306）、Terra medium（35、0.17、119） | 16 以上: Terra low（26、0.07、48）、Luna high（18、0.07、288） |
| 下位 | 13 以上: Haiku low（13、0.04、115）、Terra low（15、0.07、48） | 10 以上: Luna medium（13、0.04、未掲載）、Terra low（24、0.07、48） | 11 以上: Haiku low（11、0.04、115）、Luna medium（14、0.04、未掲載）、Terra low（26、0.07、48） |

AutomationBench は Luna・Haiku・Gemini low を除くほぼすべてが 53〜72 に収まり、ぶれ幅も小さいため、帯が max 級だけに偏る。AA-Briefcase はぶれ幅を算出できない。どちらも帯の判定には使わず、候補間の比較の補助にする。

## ぶれ幅

ぶれ幅より小さい点差は同等とみなす。同じ問題で比べる思考レベル間の差は、実際にはこれより小さい。Intelligence と AA-Briefcase は合成指標・Elo のため算出しない。

| 指標 | 問題数 × 試行回数 | ぶれ幅 |
|---|---|---:|
| Terminal-Bench | 66 × 3 | ±12 |
| FrontierCode | 132 × 3 | ±9 |
| GDP.pdf | 100 × 5 | ±10 |
| AutomationBench | 657 × 1 | ±4 |
| Omniscience | 3,000 × 1 | ±4 |

## 比較表

| モデル | effort | Intelligence | Terminal-Bench % | FrontierCode % | GDP.pdf % | AutomationBench % | AA-Briefcase | Omniscience | USD/task（参考） | 秒/task |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Luna | low | 10 | 0 | 2 | 9 | 12 | 740 | -18 | 0.01 | 26.26 |
| Luna | medium | 18 | 3 | 13 | 14 | 40 | 1096 | -14 | 0.04 | 未掲載 |
| Luna | high | 21 | 5 | 19 | 18 | 48 | 1187 | -13 | 0.07 | 287.86 |
| Luna | xhigh | 23 | 8 | 18 | 19 | 48 | 1235 | -13 | 0.10 | 362.24 |
| Luna | max | 28 | 13 | 25 | 23 | 53 | 1337 | -8 | 0.15 | 631.02 |
| Terra | low | 29 | 15 | 24 | 26 | 56 | 1030 | 23 | 0.07 | 48.25 |
| Terra | medium | 38 | 32 | 35 | 28 | 58 | 1191 | 27 | 0.17 | 118.86 |
| Terra | high | 42 | 42 | 37 | 28 | 58 | 1264 | 28 | 0.26 | 180.10 |
| Terra | xhigh | 45 | 46 | 37 | 27 | 60 | 1333 | 29 | 0.40 | 283.22 |
| Terra | max | 51 | 56 | 42 | 29 | 60 | 1402 | 30 | 0.96 | 610.15 |
| Sol | low | 35 | 31 | 20 | 27 | 53 | 1114 | 38 | 0.16 | 112.77 |
| Sol | medium | 46 | 48 | 33 | 30 | 63 | 1361 | 40 | 0.36 | 264.32 |
| Sol | high | 50 | 52 | 37 | 32 | 64 | 1467 | 41 | 0.59 | 374.61 |
| Sol | xhigh | 52 | 54 | 39 | 32 | 67 | 1502 | 42 | 0.76 | 425.70 |
| Sol | max | 55 | 56 | 41 | 31 | 65 | 1555 | 42 | 1.27 | 927.67 |
| Astra | low | 43 | 42 | 26 | 30 | 59 | 1256 | 40 | 1.42 | 156.96 |
| Astra | medium | 51 | 49 | 37 | 30 | 65 | 1462 | 41 | 2.73 | 318.19 |
| Astra | high | 55 | 54 | 40 | 31 | 67 | 1505 | 45 | 3.24 | 356.03 |
| Astra | xhigh | 55 | 60 | 41 | 32 | 67 | 1544 | 44 | 3.66 | 406.09 |
| Astra | max | 57 | 59 | 42 | 31 | 68 | 1569 | 42 | 6.24 | 658.38 |
| Haiku 5.5 | low | 19 | 13 | 8 | 11 | 23 | 1114 | 2 | 0.04 | 115.22 |
| Haiku 5.5 | medium | 25 | 15 | 16 | 15 | 29 | 1369 | 4 | 0.09 | 195.30 |
| Haiku 5.5 | high | 30 | 22 | 23 | 17 | 34 | 1441 | 5 | 0.16 | 305.72 |
| Haiku 5.5 | xhigh | 34 | 29 | 30 | 18 | 36 | 1525 | 8 | 0.25 | 466.54 |
| Haiku 5.5 | max | 36 | 33 | 35 | 21 | 35 | 1576 | 12 | 0.41 | 592.37 |
| Sonnet 5.5 | low | 25 | 21 | 7 | 16 | 49 | 1268 | 20 | 0.51 | 130.25 |
| Sonnet 5.5 | medium | 30 | 30 | 11 | 20 | 55 | 1440 | 19 | 0.78 | 192.90 |
| Sonnet 5.5 | high | 41 | 44 | 26 | 25 | 59 | 1635 | 19 | 1.64 | 352.49 |
| Sonnet 5.5 | xhigh | 50 | 57 | 36 | 25 | 66 | 1744 | 21 | 4.09 | 725.03 |
| Sonnet 5.5 | max | 54 | 64 | 42 | 26 | 72 | 1814 | 30 | 10.02 | 1298.51 |
| Fable 5.1 | low | 38 | 40 | 23 | 28 | 52 | 1479 | 34 | 4.47 | 413.73 |
| Fable 5.1 | medium | 43 | 45 | 29 | 27 | 55 | 1525 | 36 | 5.56 | 536.27 |
| Fable 5.1 | high | 47 | 52 | 30 | 27 | 55 | 1577 | 40 | 7.54 | 733.23 |
| Fable 5.1 | xhigh | 50 | 55 | 36 | 26 | 58 | 1651 | 44 | 10.85 | 970.62 |
| Fable 5.1 | max | 49 | 52 | 32 | 26 | 59 | 1670 | 46 | 12.99 | 1073.89 |
| Opus 5.5 | low | 35 | 31 | 16 | 26 | 53 | 1279 | 39 | 0.98 | 153.00 |
| Opus 5.5 | medium | 48 | 53 | 33 | 26 | 61 | 1622 | 40 | 2.45 | 346.91 |
| Opus 5.5 | high | 52 | 57 | 36 | 29 | 63 | 1682 | 42 | 3.46 | 473.90 |
| Opus 5.5 | xhigh | 57 | 60 | 44 | 27 | 65 | 1761 | 43 | 6.05 | 792.74 |
| Opus 5.5 | max | 58 | 60 | 46 | 26 | 70 | 1801 | 48 | 10.04 | 1140.78 |
| Gemini 3.8 Flash | low | 22 | 10 | 8 | 19 | 37 | 1062 | 13 | 未掲載 | 未掲載 |
| Gemini 3.8 Flash | medium | 30 | 20 | 16 | 23 | 61 | 1183 | 24 | 6.26 | 未掲載 |
| Gemini 3.8 Flash | high | 31 | 20 | 19 | 21 | 60 | 1203 | 23 | 7.77 | 785.79 |

## データの更新

- 値はサイトの表示精度で記載し、未掲載値の補間や他世代からの流用はしない。
- Codex・Claude の effort 別の値は、各モデル `<m>` の比較ページ `https://artificialanalysis.ai/models/comparisons/<m>-low-vs-<m>-medium`（low・medium）、`<m>-high-vs-<m>-xhigh`（high・xhigh）、`<m>-vs-<m>-low`（max）から取得する。`<m>` はリリースページ URL の末尾（例: `gpt-6-1-terra`、`claude-opus-5-5`）。Gemini 3.8 Flash は `gemini-3-8-flash-low-vs-gemini-3-8-flash-medium`（low・medium）と `gemini-3-8-flash-vs-gemini-3-8-flash-medium`（high）。比較ページの列は URL ではなく見出しの順に並ぶ。
- ぶれ幅は、評価方法のページが信頼区間を公表していないため、問題数を独立した標本数とみなし、反復試行は数えず、得点率 50% を仮定した二項分布の 95% 区間の半幅として概算する。
- 値を更新したら、ぶれ幅と帯ごとの目安も同じ規則で作り直す。

出典: [評価方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking)。リリースページ: [Luna](https://artificialanalysis.ai/models/releases/gpt-6-luna)、[Terra](https://artificialanalysis.ai/models/releases/gpt-6-1-terra)、[Sol](https://artificialanalysis.ai/models/releases/gpt-6-1-sol)、[Astra](https://artificialanalysis.ai/models/releases/gpt-6-astra)、[Haiku 5.5](https://artificialanalysis.ai/models/releases/claude-haiku-5-5)、[Sonnet 5.5](https://artificialanalysis.ai/models/releases/claude-sonnet-5-5)、[Fable 5.1](https://artificialanalysis.ai/models/releases/claude-fable-5-1)、[Opus 5.5](https://artificialanalysis.ai/models/releases/claude-opus-5-5)、[Gemini 3.8 Flash](https://artificialanalysis.ai/models/releases/gemini-3-8-flash)。
