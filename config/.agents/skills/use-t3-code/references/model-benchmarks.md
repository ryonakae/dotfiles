# モデル × 思考レベルの比較データ

[Artificial Analysis](https://artificialanalysis.ai/)（2026-10-31 確認）。Codex・Claude の 8 モデルは low / medium / high / xhigh / max、Gemini 3.8 Flash は low / medium / high の 5 指標・費用・時間を確認した。表はサイトの表示精度で記載し、未掲載値の補間や他世代からの流用はしない。起動ごとの再検索は不要。

- **Intelligence**: Intelligence Index v5.0。9 評価の総合指標で、成功率ではない。
- **Terminal-Bench**: Terminal-Bench 4.0。ターミナル上の複雑な作業の成功率。
- **FrontierCode**: FrontierCode 2.0。実在するリポジトリの変更をテストと評価基準で採点した平均スコア。必須条件を満たさない試行は 0 点、それ以外は部分点を含む。タスク成功率ではない。
- **GDP.pdf**: 長い業務文書を読んで回答する評価。すべての評価基準を満たした試行の割合（All-pass）。検索・ツールは使わず、対応モデルにはページ画像も渡す。リポジトリ探索やコードの依存関係追跡を直接測るものではない。
- **Omniscience**: AA-Omniscience v1.1 Net Score（−100〜100）。正答を加点、誤答を減点し、回答保留は減点しない。検索能力ではない。
- **USD/task**: Intelligence Index の評価タスクあたり加重平均費用。T3 での実作業費用やサブスクリプションの消費量ではない。
- **秒/task**: 比較ページの「Time per Task」。評価タスクあたりの加重平均 decode 時間で、初回トークン待ち・その他の処理時間は含まない。低い方がよい。T3 での実測完了時間ではない。「未掲載」は 0 秒ではなく、速度比較の根拠にしない。

5 指標はすべて高い方がよい。個別 4 評価は Intelligence の構成要素でもあるが、Omniscience は Net Score ではなく Accuracy と Non-Hallucination Rate が組み込まれる。主に英語・テキストで、一部は画像を含む評価である。Claude 系の行はサイト上の「(effort, Default Fallback)」バリアントの値である（Haiku 5.5 は Fallback 表記なし）。

| モデル | effort | Intelligence | Terminal-Bench % | FrontierCode % | GDP.pdf % | Omniscience | USD/task（参考） | 秒/task |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Luna | low | 10 | 0 | 2 | 9 | -18 | 0.01 | 26.26 |
| Luna | medium | 18 | 3 | 13 | 14 | -14 | 0.04 | 未掲載 |
| Luna | high | 21 | 5 | 19 | 18 | -13 | 0.07 | 287.86 |
| Luna | xhigh | 23 | 8 | 18 | 19 | -13 | 0.10 | 362.24 |
| Luna | max | 28 | 13 | 25 | 23 | -8 | 0.15 | 631.02 |
| Terra | low | 29 | 15 | 24 | 26 | 23 | 0.07 | 48.25 |
| Terra | medium | 38 | 32 | 35 | 28 | 27 | 0.17 | 118.86 |
| Terra | high | 42 | 42 | 37 | 28 | 28 | 0.26 | 180.10 |
| Terra | xhigh | 45 | 46 | 37 | 27 | 29 | 0.40 | 283.22 |
| Terra | max | 51 | 56 | 42 | 29 | 30 | 0.96 | 610.15 |
| Sol | low | 35 | 31 | 20 | 27 | 38 | 0.16 | 112.77 |
| Sol | medium | 46 | 48 | 33 | 30 | 40 | 0.36 | 264.32 |
| Sol | high | 50 | 52 | 37 | 32 | 41 | 0.59 | 374.61 |
| Sol | xhigh | 52 | 54 | 39 | 32 | 42 | 0.76 | 425.70 |
| Sol | max | 55 | 56 | 41 | 31 | 42 | 1.27 | 927.67 |
| Astra | low | 43 | 42 | 26 | 30 | 40 | 1.42 | 156.96 |
| Astra | medium | 51 | 49 | 37 | 30 | 41 | 2.73 | 318.19 |
| Astra | high | 55 | 54 | 40 | 31 | 45 | 3.24 | 356.03 |
| Astra | xhigh | 55 | 60 | 41 | 32 | 44 | 3.66 | 406.09 |
| Astra | max | 57 | 59 | 42 | 31 | 42 | 6.24 | 658.38 |
| Haiku 5.5 | low | 19 | 13 | 8 | 11 | 2 | 0.04 | 115.22 |
| Haiku 5.5 | medium | 25 | 15 | 16 | 15 | 4 | 0.09 | 195.30 |
| Haiku 5.5 | high | 30 | 22 | 23 | 17 | 5 | 0.16 | 305.72 |
| Haiku 5.5 | xhigh | 34 | 29 | 30 | 18 | 8 | 0.25 | 466.54 |
| Haiku 5.5 | max | 36 | 33 | 35 | 21 | 12 | 0.41 | 592.37 |
| Sonnet 5.5 | low | 25 | 21 | 7 | 16 | 20 | 0.51 | 130.25 |
| Sonnet 5.5 | medium | 30 | 30 | 11 | 20 | 19 | 0.78 | 192.90 |
| Sonnet 5.5 | high | 41 | 44 | 26 | 25 | 19 | 1.64 | 352.49 |
| Sonnet 5.5 | xhigh | 50 | 57 | 36 | 25 | 21 | 4.09 | 725.03 |
| Sonnet 5.5 | max | 54 | 64 | 42 | 26 | 30 | 10.02 | 1298.51 |
| Fable 5.1 | low | 38 | 40 | 23 | 28 | 34 | 4.47 | 413.73 |
| Fable 5.1 | medium | 43 | 45 | 29 | 27 | 36 | 5.56 | 536.27 |
| Fable 5.1 | high | 47 | 52 | 30 | 27 | 40 | 7.54 | 733.23 |
| Fable 5.1 | xhigh | 50 | 55 | 36 | 26 | 44 | 10.85 | 970.62 |
| Fable 5.1 | max | 49 | 52 | 32 | 26 | 46 | 12.99 | 1073.89 |
| Opus 5.5 | low | 35 | 31 | 16 | 26 | 39 | 0.98 | 153.00 |
| Opus 5.5 | medium | 48 | 53 | 33 | 26 | 40 | 2.45 | 346.91 |
| Opus 5.5 | high | 52 | 57 | 36 | 29 | 42 | 3.46 | 473.90 |
| Opus 5.5 | xhigh | 57 | 60 | 44 | 27 | 43 | 6.05 | 792.74 |
| Opus 5.5 | max | 58 | 60 | 46 | 26 | 48 | 10.04 | 1140.78 |
| Gemini 3.8 Flash | low | 22 | 10 | 8 | 19 | 13 | 未掲載 | 未掲載 |
| Gemini 3.8 Flash | medium | 30 | 20 | 16 | 23 | 24 | 6.26 | 未掲載 |
| Gemini 3.8 Flash | high | 31 | 20 | 19 | 21 | 23 | 7.77 | 785.79 |

出典: [評価方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking)。各モデルのリリースページ: [Luna](https://artificialanalysis.ai/models/releases/gpt-6-luna)、[Terra](https://artificialanalysis.ai/models/releases/gpt-6-1-terra)、[Sol](https://artificialanalysis.ai/models/releases/gpt-6-1-sol)、[Astra](https://artificialanalysis.ai/models/releases/gpt-6-astra)、[Haiku 5.5](https://artificialanalysis.ai/models/releases/claude-haiku-5-5)、[Sonnet 5.5](https://artificialanalysis.ai/models/releases/claude-sonnet-5-5)、[Fable 5.1](https://artificialanalysis.ai/models/releases/claude-fable-5-1)、[Opus 5.5](https://artificialanalysis.ai/models/releases/claude-opus-5-5)。

Codex・Claude の effort 別の値は、各モデル `<m>` の比較ページ `https://artificialanalysis.ai/models/comparisons/<m>-low-vs-<m>-medium`（low・medium）、`<m>-high-vs-<m>-xhigh`（high・xhigh）、`<m>-vs-<m>-low`（max）から取得した。`<m>` はリリースページ URL の末尾（例: `gpt-6-1-terra`、`claude-opus-5-5`）。比較ページの列は URL ではなく見出しの順に並ぶ。

Gemini 3.8 Flash: [リリースページ](https://artificialanalysis.ai/models/releases/gemini-3-8-flash)、[low・medium](https://artificialanalysis.ai/models/comparisons/gemini-3-8-flash-low-vs-gemini-3-8-flash-medium)、[high・medium](https://artificialanalysis.ai/models/comparisons/gemini-3-8-flash-vs-gemini-3-8-flash-medium)。評価値は Google のモデルのもので、Antigravity 経由の実測ではない。文章作成での優先方針は [delegation.md](delegation.md) に従う。
