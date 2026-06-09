# 日本語タイポグラフィ拡張ガイド

## 適用条件

対象サイトや VI に日本語コンテンツが含まれる場合、Typography Rules セクションに以下の項目を追加する。
英語のみのプロジェクトには適用しない。

判断基準: サイトのHTMLに日本語テキストがある、PDF に日本語の文字がある、リポジトリに日本語フォントの指定がある、のいずれかで適用する。

---

## 1. 和文フォントの指定

### 原則
- 和文フォントを先に指定する（日本語表示品質を優先するため）
- 欧文フォントは和文グリフより優先したい場合のみ先に置く
- 最後に generic family（sans-serif / serif）を指定する

### フォールバックチェーンの例

```css
/* ゴシック系（モダンで読みやすい） */
font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Hiragino Sans", "ヒラギノ角ゴ Pro W3", "メイリオ", "Meiryo", sans-serif;

/* 明朝系（格調ある・読み物系） */
font-family: "Noto Serif JP", "Hiragino Mincho ProN", "游明朝", "Yu Mincho", serif;

/* 欧文を優先したい場合（見出し等） */
font-family: "Inter", "Noto Sans JP", sans-serif;
```

### DESIGN.md への記述形式
```
- 和文フォント: "Noto Sans JP"（本文）, "Noto Serif JP"（引用・強調）
- フォールバック: "Hiragino Kaku Gothic ProN", "メイリオ", sans-serif
```

---

## 2. 行間（line-height）

和文は欧文より広い行間が必要（縦方向の密度が高いため）。

| 用途 | 推奨値 | 理由 |
|------|--------|------|
| 本文 | 1.7 〜 2.0 | 縦方向の密度を下げて可読性を確保 |
| 見出し | 1.2 〜 1.4 | タイトル要素は詰め気味が映える |
| 補助テキスト | 1.5 〜 1.7 | 本文より少し狭くてよい |
| キャプション | 1.5 | 小さい文字は特に行間が必要 |

**最低ライン: 本文 1.5 以上（1.2 以下は可読性が著しく低下するため禁止）**

---

## 3. 字間（letter-spacing）

```css
/* 本文: ほんの少し広げる */
letter-spacing: 0.04em;

/* 見出し: 0 または詰め気味 */
letter-spacing: 0em;

/* 英数字混在の注意点 */
/* letter-spacing は英数字にも適用される。欧文フォントのカーニングを壊す場合がある */
```

| 用途 | 推奨値 |
|------|--------|
| 本文（日本語主体） | 0.04em |
| 見出し | 0 〜 -0.01em |
| 全角英数字 | 0em |

---

## 4. 禁則処理

```css
/* 基本設定 */
word-break: break-all;      /* 折り返し可能位置で改行 */
overflow-wrap: break-word;  /* 長い単語の折り返し */
line-break: strict;         /* 句読点の行頭禁止（厳密ルール） */
```

**行頭に置けない文字（行末禁則）:** `）」』】〕〉》、。，．・：；？！`
**行末に置けない文字（行頭禁則）:** `（「『【〔〈《`

`line-break: strict` を指定すれば多くのブラウザが自動処理する。

---

## 5. OpenType 機能

```css
/* palt: プロポーショナルメトリクス（字詰め） */
/* 見出し・ナビゲーション・ボタンラベル等で有効 */
/* 本文では慎重に（可読性が低下する場合がある） */
font-feature-settings: "palt" 1;

/* kern: カーニング */
/* 和欧混植テキストで有効 */
font-feature-settings: "kern" 1;

/* 同時使用 */
font-feature-settings: "palt" 1, "kern" 1;
```

| 機能 | 適用箇所 | 注意 |
|------|----------|------|
| palt | 見出し、ナビゲーション、ボタン | 本文は設計者判断 |
| kern | 和欧混植テキスト全般 | 通常は有効にしてよい |

---

## 6. DESIGN.md への追記例

Typography Rules セクションの末尾に以下を追加する:

```markdown
### Japanese Typography
- 和文フォント: "Noto Sans JP"（本文）, "Noto Serif JP"（見出し）
- フォールバック: "Hiragino Kaku Gothic ProN", "メイリオ", sans-serif
- 行間: 本文 1.8、見出し 1.3、補助テキスト 1.6
- 字間: 本文 0.04em、見出し 0em
- 禁則処理: line-break: strict（句読点の行頭/行末禁止）
- OpenType: 見出しで palt 有効、和欧混植テキストで kern 有効
```
