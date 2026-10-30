# モデル × 思考レベルの比較データ

[Artificial Analysis](https://artificialanalysis.ai/)（2026-10-27 確認）。8 モデルとも low / medium / high / xhigh / max の 4 指標・費用・時間を取得した。表はサイトの表示精度で記載し、未掲載値の補間や他世代からの流用はしない。起動ごとの再検索は不要。

- **Intelligence**: Intelligence Index v4.3.2。10 評価の総合指標で、成功率ではない。
- **Terminal-Bench**: Terminal-Bench 4.0。ターミナル上の複雑な作業の成功率。
- **AA-LCR**: AA-LCR v1.1。長文資料の抽出・推論・統合の正答率。リポジトリ探索やコードの依存関係追跡を直接測るものではない。
- **Omniscience**: AA-Omniscience Index（−100〜100）。正答を加点、誤答を減点し、回答保留は減点しない。検索能力ではない。
- **USD/task**: Intelligence Index の評価タスクあたり加重平均費用。T3 での実作業費用やサブスクリプションの消費量ではない。
- **秒/task**: 比較ページの「Time per Task」。低い方がよい。T3 での実測完了時間ではない。「未掲載」は 0 秒ではなく、速度比較の根拠にしない。

4 指標はすべて高い方がよい。個別 3 評価は Intelligence の構成要素でもある。主に英語・テキストでの評価である。Claude 系の行はサイト上の「(effort, Default Fallback)」バリアントの値である（Haiku 5.5 は Fallback 表記なし）。

| モデル | effort | Intelligence | Terminal-Bench % | AA-LCR % | Omniscience | USD/task（参考） | 秒/task |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna | low | 22 | 0 | 74 | -9 | 0.0045 | 17.78 |
| Luna | medium | 30 | 3 | 78 | -5 | 0.02 | 未掲載 |
| Luna | high | 33 | 5 | 79 | -6 | 0.03 | 162.57 |
| Luna | xhigh | 35 | 8 | 80 | -2 | 0.04 | 218.80 |
| Luna | max | 38 | 13 | 83 | 1 | 0.07 | 396.74 |
| Terra | low | 36 | 15 | 81 | 24 | 0.05 | 29.28 |
| Terra | medium | 41 | 32 | 81 | 27 | 0.10 | 63.34 |
| Terra | high | 44 | 42 | 82 | 28 | 0.13 | 95.90 |
| Terra | xhigh | 45 | 46 | 82 | 29 | 0.19 | 159.39 |
| Terra | max | 48 | 56 | 83 | 30 | 0.40 | 384.85 |
| Sol | low | 42 | 31 | 84 | 38 | 0.13 | 75.06 |
| Sol | medium | 48 | 48 | 83 | 40 | 0.21 | 151.17 |
| Sol | high | 50 | 52 | 82 | 41 | 0.32 | 206.37 |
| Sol | xhigh | 51 | 54 | 80 | 41 | 0.39 | 270.67 |
| Sol | max | 52 | 56 | 83 | 42 | 0.72 | 500.67 |
| Astra | low | 46 | 42 | 80 | 41 | 0.82 | 85.58 |
| Astra | medium | 50 | 49 | 80 | 42 | 1.54 | 161.34 |
| Astra | high | 51 | 54 | 80 | 44 | 1.73 | 184.51 |
| Astra | xhigh | 52 | 60 | 80 | 43 | 2.31 | 247.91 |
| Astra | max | 53 | 59 | 81 | 43 | 3.26 | 398.61 |
| Haiku 5.5 | low | 29 | 13 | 72 | 3 | 0.02 | 61.48 |
| Haiku 5.5 | medium | 34 | 15 | 77 | 4 | 0.05 | 119.37 |
| Haiku 5.5 | high | 38 | 22 | 77 | 6 | 0.08 | 191.56 |
| Haiku 5.5 | xhigh | 41 | 29 | 78 | 6 | 0.12 | 289.51 |
| Haiku 5.5 | max | 43 | 33 | 83 | 11 | 0.21 | 426.25 |
| Sonnet 5.5 | low | 36 | 21 | 76 | 19 | 0.35 | 83.41 |
| Sonnet 5.5 | medium | 41 | 30 | 76 | 20 | 0.48 | 121.21 |
| Sonnet 5.5 | high | 47 | 44 | 78 | 21 | 0.88 | 215.21 |
| Sonnet 5.5 | xhigh | 52 | 57 | 80 | 24 | 2.01 | 422.84 |
| Sonnet 5.5 | max | 56 | 64 | 83 | 32 | 5.46 | 916.69 |
| Fable 5.1 | low | 47 | 40 | 82 | 34 | 2.37 | 234.30 |
| Fable 5.1 | medium | 49 | 45 | 85 | 38 | 2.98 | 294.84 |
| Fable 5.1 | high | 51 | 52 | 84 | 41 | 3.91 | 407.00 |
| Fable 5.1 | xhigh | 53 | 55 | 83 | 42 | 5.98 | 597.63 |
| Fable 5.1 | max | 53 | 52 | 85 | 43 | 7.63 | 741.39 |
| Opus 5.5 | low | 42 | 31 | 81 | 39 | 0.55 | 78.78 |
| Opus 5.5 | medium | 51 | 53 | 84 | 40 | 1.34 | 198.00 |
| Opus 5.5 | high | 54 | 57 | 83 | 41 | 1.82 | 278.68 |
| Opus 5.5 | xhigh | 56 | 60 | 85 | 43 | 3.46 | 500.00 |
| Opus 5.5 | max | 58 | 60 | 85 | 46 | 5.98 | 774.81 |

出典: [評価方法](https://artificialanalysis.ai/methodology/intelligence-benchmarking)。各モデルのリリースページ: [Luna](https://artificialanalysis.ai/models/releases/gpt-6-luna)、[Terra](https://artificialanalysis.ai/models/releases/gpt-6-1-terra)、[Sol](https://artificialanalysis.ai/models/releases/gpt-6-1-sol)、[Astra](https://artificialanalysis.ai/models/releases/gpt-6-astra)、[Haiku 5.5](https://artificialanalysis.ai/models/releases/claude-haiku-5-5)、[Sonnet 5.5](https://artificialanalysis.ai/models/releases/claude-sonnet-5-5)、[Fable 5.1](https://artificialanalysis.ai/models/releases/claude-fable-5-1)、[Opus 5.5](https://artificialanalysis.ai/models/releases/claude-opus-5-5)。

effort 別の値は、各モデル `<m>` の比較ページ `https://artificialanalysis.ai/models/comparisons/<m>-low-vs-<m>-medium`（low・medium）、`<m>-high-vs-<m>-xhigh`（high・xhigh）、`<m>-vs-<m>-low`（max）から取得した。`<m>` はリリースページ URL の末尾（例: `gpt-6-1-terra`、`claude-opus-5-5`）。比較ページの列は URL ではなく見出しの順に並ぶ。
