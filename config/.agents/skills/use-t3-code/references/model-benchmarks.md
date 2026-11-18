# モデル × 思考レベルの比較データ

[Artificial Analysis](https://artificialanalysis.ai/) の値。GPT-6.2 Sol・GPT-6.2 Astra・Claude Fable 5.2 と Codex・Claude Code での評価は 2026-11-18 確認。その他の値は 2026-10-31 確認（AutomationBench・AA-Briefcase は 2026-11-03 確認）。起動ごとの再検索は不要。Gemini 3.8 Flash の値は Google のモデルのもので、Antigravity 経由の実測ではない。

内容: 指標、クラス、ぶれ幅、比較表、Codex・Claude Code での評価、データの更新（値を更新するときだけ読む）。

## 指標

- **Intelligence**: Intelligence Index v5.0（2026-11-18 確認分は v5.0.1）。9 評価の総合指標で、成功率ではない。
- **Terminal-Bench**: Terminal-Bench 4.0。ターミナル上の複雑な作業の成功率。
- **FrontierCode**: FrontierCode 2.0。実在するリポジトリの変更をテストと評価基準で採点した平均スコア。必須条件を満たさない試行は 0 点、それ以外は部分点を含む。タスク成功率ではない。
- **GDP.pdf**: 長い業務文書を読んで回答する評価。すべての評価基準を満たした試行の割合（All-pass）。検索・ツールは使わず、対応モデルにはページ画像も渡す。リポジトリ探索やコードの依存関係追跡を直接測るものではない。
- **AutomationBench**: AutomationBench-AA。Gmail・Slack・Jira などを模した複数の SaaS を REST API のツール呼び出しで操作する業務フローの評価。最終状態をプログラムで検査し、達成した目標の割合を採点する。禁止事項に違反した試行は 0 点。
- **AA-Briefcase**: 数千の資料を入力にした、複数週にわたる知識作業プロジェクトの評価。成果物を評価基準と一対比較で採点した Elo で、成功率ではない。
- **Omniscience**: AA-Omniscience v1.1 Net Score（−100〜100）。正答を加点、誤答を減点し、回答保留は減点しない。検索能力ではない。
- **USD/task**: Intelligence Index の評価タスクあたり加重平均費用。単価とトークン量の積で、T3 での実作業費用やサブスクリプションの消費量ではない。provider ごとに使用量枠が別のため、値をそのまま provider をまたいで比べず、価格比の計算にだけ使う。
- **秒/task**: 比較ページの「Time per Task」。評価タスクの出力トークン数と出力速度から算出した加重平均時間。2026-11-18 確認分は比較ページの分表示を秒に換算した値。取得時期が異なる値の小差で優劣を決めない。「未掲載」は速度比較に使わない。

7 指標はすべて高い方がよい。主に英語・テキストの評価で、一部は画像を含む。Claude 系の行はサイト上の「(effort, Default Fallback)」バリアントの値である（Claude Haiku 5.5 は Fallback 表記なし）。

## クラス

[delegation.md の選定手順](delegation.md#共通の選定手順) で、作業の難度に対応させる。各モデルの medium の USD/task を、比較対象のうち同じ provider で最も高いモデルの値で割った価格比で分ける。価格比は provider のラインナップ上の位置を表し、同じ使用量枠の中での消費の大小の目安になる。境界は価格比が大きく開く箇所に置き、判定には丸める前の値を使う。

| クラス | 価格比 | 該当（価格比） |
|---|---|---|
| 軽量 | 0.12 未満 | Claude Haiku 5.5（0.02）、GPT-6 Luna（0.03）、GPT-6.1 Terra（0.10） |
| 標準 | 0.12 以上 0.3 未満 | Claude Sonnet 5.5（0.21）、GPT-6.2 Sol（0.25） |
| 最上位 | 0.3 以上 | Claude Opus 5.5（0.64）、GPT-6.2 Astra（1）、Claude Fable 5.2（1） |

比較対象が 1 モデルしかない provider（Gemini 3.8 Flash）はクラスに入れない。同じクラスの候補をコストで比べるときは、各組み合わせの USD/task を同じ基準値で割った価格比を使う（例: GPT-6.2 Sol medium 0.25、Claude Sonnet 5.5 high 0.43）。

軽量クラスの下限は、ぶれ幅を超える値とする。まったく機能しない組み合わせと区別できる水準である。下限を満たす組み合わせを秒/task の小さい順に並べた。括弧内は指標の値・秒/task。

| 指標 | 下限 | 組み合わせ |
|---|---|---|
| Terminal-Bench | 13 以上 | GPT-6.1 Terra low（15、48）、Claude Haiku 5.5 low（13、115）、GPT-6.1 Terra medium（32、119） |
| FrontierCode | 10 以上 | GPT-6.1 Terra low（24、48）、GPT-6.1 Terra medium（35、119）、Claude Haiku 5.5 medium（16、195） |
| GDP.pdf | 11 以上 | GPT-6.1 Terra low（26、48）、Claude Haiku 5.5 low（11、115）、GPT-6.1 Terra medium（28、119） |

AutomationBench・AA-Briefcase は候補間の比較の補助にし、下限の判定には使わない。

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

`—` は更新時に参照した比較ページで値を確認できなかった項目。

| モデル | effort | Intelligence | Terminal-Bench % | FrontierCode % | GDP.pdf % | AutomationBench % | AA-Briefcase | Omniscience | USD/task（参考） | 秒/task |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-6 Luna | low | 10 | 0 | 2 | 9 | 12 | 740 | -18 | 0.01 | 26.26 |
| GPT-6 Luna | medium | 18 | 3 | 13 | 14 | 40 | 1096 | -14 | 0.04 | 未掲載 |
| GPT-6 Luna | high | 21 | 5 | 19 | 18 | 48 | 1187 | -13 | 0.07 | 287.86 |
| GPT-6 Luna | xhigh | 23 | 8 | 18 | 19 | 48 | 1235 | -13 | 0.10 | 362.24 |
| GPT-6 Luna | max | 28 | 13 | 25 | 23 | 53 | 1337 | -8 | 0.15 | 631.02 |
| GPT-6.1 Terra | low | 29 | 15 | 24 | 26 | 56 | 1030 | 23 | 0.07 | 48.25 |
| GPT-6.1 Terra | medium | 38 | 32 | 35 | 28 | 58 | 1191 | 27 | 0.17 | 118.86 |
| GPT-6.1 Terra | high | 42 | 42 | 37 | 28 | 58 | 1264 | 28 | 0.26 | 180.10 |
| GPT-6.1 Terra | xhigh | 45 | 46 | 37 | 27 | 60 | 1333 | 29 | 0.40 | 283.22 |
| GPT-6.1 Terra | max | 51 | 56 | 42 | 29 | 60 | 1402 | 30 | 0.96 | 610.15 |
| GPT-6.2 Sol | low | 41 | 37.9 | 31.4 | 28.6 | 63.2 | 1230 | — | 0.18 | 84 |
| GPT-6.2 Sol | medium | 53 | 56.1 | 41.4 | 29.2 | 70.3 | 1498 | — | 0.41 | 186 |
| GPT-6.2 Sol | high | 55 | 58.6 | 40.2 | 28.8 | 69.9 | 1540 | — | 0.56 | 252 |
| GPT-6.2 Sol | xhigh | 56 | 56.1 | 42.8 | 28.4 | 70.6 | 1577 | — | 0.65 | 306 |
| GPT-6.2 Sol | max | 57 | 60.1 | 44.4 | 30.0 | 71.3 | 1612 | — | 1.01 | 474 |
| GPT-6.2 Astra | low | 46 | 51.0 | 32.7 | 28.0 | 68.6 | 1038 | — | 0.66 | 90 |
| GPT-6.2 Astra | medium | 57 | 58.6 | 46.6 | 28.4 | 72.8 | 1409 | — | 1.62 | 222 |
| GPT-6.2 Astra | high | 60 | 60.1 | 47.1 | 28.6 | 76.0 | 1570 | — | 2.07 | 294 |
| GPT-6.2 Astra | xhigh | 62 | 64.1 | 49.0 | 28.0 | 76.1 | 1594 | — | 2.52 | 372 |
| GPT-6.2 Astra | max | 62 | 64.1 | 45.4 | 29.8 | 77.2 | 1643 | — | 4.00 | 642 |
| Claude Haiku 5.5 | low | 19 | 13 | 8 | 11 | 23 | 1114 | 2 | 0.04 | 115.22 |
| Claude Haiku 5.5 | medium | 25 | 15 | 16 | 15 | 29 | 1369 | 4 | 0.09 | 195.30 |
| Claude Haiku 5.5 | high | 30 | 22 | 23 | 17 | 34 | 1441 | 5 | 0.16 | 305.72 |
| Claude Haiku 5.5 | xhigh | 34 | 29 | 30 | 18 | 36 | 1525 | 8 | 0.25 | 466.54 |
| Claude Haiku 5.5 | max | 36 | 33 | 35 | 21 | 35 | 1576 | 12 | 0.41 | 592.37 |
| Claude Sonnet 5.5 | low | 25 | 21 | 7 | 16 | 49 | 1268 | 20 | 0.51 | 130.25 |
| Claude Sonnet 5.5 | medium | 30 | 30 | 11 | 20 | 55 | 1440 | 19 | 0.78 | 192.90 |
| Claude Sonnet 5.5 | high | 41 | 44 | 26 | 25 | 59 | 1635 | 19 | 1.64 | 352.49 |
| Claude Sonnet 5.5 | xhigh | 50 | 57 | 36 | 25 | 66 | 1744 | 21 | 4.09 | 725.03 |
| Claude Sonnet 5.5 | max | 54 | 64 | 42 | 26 | 72 | 1814 | 30 | 10.02 | 1298.51 |
| Claude Fable 5.2 | low | 54 | 54.5 | 38.4 | 26.8 | 68.0 | 1563 | — | 3.10 | 318 |
| Claude Fable 5.2 | medium | 56 | 55.1 | 41.3 | 23.8 | 68.8 | 1622 | — | 3.80 | 384 |
| Claude Fable 5.2 | high | 62 | 59.6 | 49.1 | 21.8 | 71.4 | 1677 | — | 9.08 | 888 |
| Claude Fable 5.2 | xhigh | 62 | 61.6 | 47.6 | 21.4 | 74.2 | 1737 | — | 14.83 | 1428 |
| Claude Fable 5.2 | max | 65 | 59.6 | 48.8 | 24.2 | 76.4 | 1785 | — | 26.54 | 2442 |
| Claude Opus 5.5 | low | 35 | 31 | 16 | 26 | 53 | 1279 | 39 | 0.98 | 153.00 |
| Claude Opus 5.5 | medium | 48 | 53 | 33 | 26 | 61 | 1622 | 40 | 2.45 | 346.91 |
| Claude Opus 5.5 | high | 52 | 57 | 36 | 29 | 63 | 1682 | 42 | 3.46 | 473.90 |
| Claude Opus 5.5 | xhigh | 57 | 60 | 44 | 27 | 65 | 1761 | 43 | 6.05 | 792.74 |
| Claude Opus 5.5 | max | 58 | 60 | 46 | 26 | 70 | 1801 | 48 | 10.04 | 1140.78 |
| Gemini 3.8 Flash | low | 22 | 10 | 8 | 19 | 37 | 1062 | 13 | 未掲載 | 未掲載 |
| Gemini 3.8 Flash | medium | 30 | 20 | 16 | 23 | 61 | 1183 | 24 | 6.26 | 未掲載 |
| Gemini 3.8 Flash | high | 31 | 20 | 19 | 21 | 60 | 1203 | 23 | 7.77 | 785.79 |

## Codex・Claude Code での評価

Artificial Analysis が各ハーネスで計測した値。Terminal-Bench は 4.1、費用と時間はエージェントの平均で、モデル単体の比較表とは計測条件が異なる。SWE-Atlas-QnA-AA はリポジトリに関する質問への回答を測る。[Claude Code と Codex の比較](https://artificialanalysis.ai/agents/coding-agents/comparisons/claude-code-vs-codex)

| モデル | effort | FrontierCode | Terminal-Bench | SWE-Atlas-QnA | USD/task | 分/task |
|---|---|---:|---:|---:|---:|---:|
| GPT-6.2 Sol | low | 28 | 41 | 42 | 0.33 | 7.2 |
| GPT-6.2 Sol | medium | 36 | 49 | 50 | 0.57 | 8.4 |
| GPT-6.2 Sol | high | 38 | 54 | 51 | 0.76 | 10.6 |
| GPT-6.2 Astra | medium | 40 | 54 | 54 | 1.20 | 11.6 |
| GPT-6.2 Astra | high | 42 | 60 | 55 | 2.37 | 15.8 |
| Claude Fable 5.2 | medium | 36 | 60 | 64 | 2.89 | 15.1 |
| Claude Fable 5.2 | high | 49 | 64 | 62 | 7.51 | 31.3 |
| Claude Fable 5.2 | xhigh | 49 | 64 | 62 | 15.47 | 53.3 |

- GPT-6.2 Sol は low から medium で 3 指標がそれぞれ 8 点上がり、medium から high での上昇は最大 5 点。通常作業には medium を使う。
- GPT-6.2 Astra は medium から high で Terminal-Bench が 6 点上がる。難度の高い環境操作や複数の工程を含む作業では high を起点にする。
- Claude Fable 5.2 は medium から high で FrontierCode が 13 点上がる。リポジトリの変更が難所なら high を使う。xhigh は 3 指標とも high と同点だった。

## データの更新

- 値はサイトの表示精度で記載し、未掲載値の補間や他世代からの流用はしない。
- 2026-11-18 確認分は [GPT-6.2 Astra と GPT-6.2 Sol のリリース比較](https://artificialanalysis.ai/de/models/comparisons/gpt-6-2-astra-vs-gpt-6-2-sol)と [Claude Fable 5.2 と Claude Sonnet 5.5 のリリース比較](https://artificialanalysis.ai/models/comparisons/claude-fable-5-2-vs-claude-sonnet-5-5)から取得した。
- その他の Codex・Claude の effort 別の値は、各モデル `<m>` の比較ページ `https://artificialanalysis.ai/models/comparisons/<m>-low-vs-<m>-medium`（low・medium）、`<m>-high-vs-<m>-xhigh`（high・xhigh）、`<m>-vs-<m>-low`（max）から取得する。`<m>` はリリースページ URL の末尾（例: `gpt-6-1-terra`、`claude-opus-5-5`）。Gemini 3.8 Flash は `gemini-3-8-flash-low-vs-gemini-3-8-flash-medium`（low・medium）と `gemini-3-8-flash-vs-gemini-3-8-flash-medium`（high）。比較ページの列は URL ではなく見出しの順に並ぶ。
- ぶれ幅は、評価方法のページが信頼区間を公表していないため、問題数を独立した標本数とみなし、反復試行は数えず、得点率 50% を仮定した二項分布の 95% 区間の半幅として概算する。
- 値を更新したら、ぶれ幅・クラス・軽量クラスの下限も同じ規則で作り直し、[サブエージェントの既定モデル・思考レベル](../SKILL.md#サブエージェントの既定モデル思考レベル)も選定手順で選び直す。

出典: [評価方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking)。リリースページ: [GPT-6 Luna](https://artificialanalysis.ai/models/releases/gpt-6-luna)、[GPT-6.1 Terra](https://artificialanalysis.ai/models/releases/gpt-6-1-terra)、[GPT-6.2 Sol](https://artificialanalysis.ai/models/gpt-6-2-sol)、[GPT-6.2 Astra](https://artificialanalysis.ai/models/gpt-6-2-astra)、[Claude Haiku 5.5](https://artificialanalysis.ai/models/releases/claude-haiku-5-5)、[Claude Sonnet 5.5](https://artificialanalysis.ai/models/releases/claude-sonnet-5-5)、[Claude Fable 5.2](https://artificialanalysis.ai/models/claude-fable-5-2)、[Claude Opus 5.5](https://artificialanalysis.ai/models/releases/claude-opus-5-5)、[Gemini 3.8 Flash](https://artificialanalysis.ai/models/releases/gemini-3-8-flash)。
