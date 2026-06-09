# DESIGN.md テンプレートと記述ガイド

## 使い方

- このファイルは DESIGN.md の構造と各セクションの書き方を定義する
- セクションヘッダーは英語のまま使う（AIエージェントの可読性のため）
- 値の説明は日本語でもOK
- 各セクション末の「記述ガイド」に従い、入力ソースから抽出した実際の値で埋める

---

## テンプレート

```markdown
# Design System: [プロジェクト名]

## 1. Visual Theme & Atmosphere
[ブランドの全体的な視覚的印象を1-2段落で記述]

Key Characteristics:
- [特徴1]
- [特徴2]
- [特徴3]

## 2. Color Palette & Roles

### Primary
- **[セマンティック名]** ([hex]) — [機能的役割]

### Secondary / Accent
- **[セマンティック名]** ([hex]) — [機能的役割]

### Semantic
- **Success [名前]** ([hex]) — 成功通知、完了状態
- **Warning [名前]** ([hex]) — 警告バナー、注意アイコン
- **Error [名前]** ([hex]) — エラーメッセージ、必須マーク
- **Info [名前]** ([hex]) — 情報バナー

### Neutrals & Surfaces
- **Surface [名前]** ([hex]) — カード背景、入力フィールド背景
- **Background [名前]** ([hex]) — ページ背景
- **Border [名前]** ([hex]) — 区切り線、入力ボーダー
- **Text Primary [名前]** ([hex]) — 見出し、本文
- **Text Secondary [名前]** ([hex]) — 補助テキスト、プレースホルダー
- **Text Disabled [名前]** ([hex]) — 無効状態のテキスト

## 3. Typography Rules

- Font Family: [フォントファミリー名], [フォールバック]
- Base Size: [px]

| Role       | Size | Weight | Line Height | Use              |
|------------|------|--------|-------------|------------------|
| Heading 1  | [px] | [wt]   | [値]        | [用途]           |
| Heading 2  | [px] | [wt]   | [値]        | [用途]           |
| Heading 3  | [px] | [wt]   | [値]        | [用途]           |
| Body       | [px] | [wt]   | [値]        | [用途]           |
| Small      | [px] | [wt]   | [値]        | [用途]           |
| Caption    | [px] | [wt]   | [値]        | [用途]           |

## 4. Component Stylings

### Buttons
- **Primary**: 背景 [色名] ([hex])、文字 [色名] ([hex])、角丸 [自然言語] ([px])、影 [自然言語]
- **Secondary**: [同様に記述]
- **Ghost / Outline**: [同様に記述]
- **Disabled**: 背景 [色名]、文字 [色名]、操作不可

### Cards
- 背景: [色名] ([hex])、角丸: [自然言語] ([px])、影: [自然言語] ([box-shadow値])
- ボーダー: [あり/なし、ある場合は値]

### Inputs
- ボーダー: [値]、角丸: [自然言語] ([px])
- フォーカス時: [スタイル]、エラー時: [スタイル]、無効時: [スタイル]

### Navigation
- [ナビゲーション固有のスタイル]

## 5. Layout Principles

- Base Spacing Unit: [px]
- Spacing Scale: [値の一覧、例: 4, 8, 16, 24, 32, 48, 64px]
- Container Max Width: [px]
- Grid: [カラム数、ガター]
- Whitespace Philosophy: [余白に対する設計思想]

## 6. Depth & Elevation

- **Level 0 (Flat)**: 影なし — [用途]
- **Level 1 (Subtle)**: [box-shadow値] — [用途]
- **Level 2 (Medium)**: [box-shadow値] — [用途]
- **Level 3 (Strong)**: [box-shadow値] — [用途]

## 7. Do's and Don'ts

### Do
- [具体的な推奨行動1]
- [具体的な推奨行動2]
- [具体的な推奨行動3]

### Don't
- [具体的な禁止行動1とその理由]
- [具体的な禁止行動2とその理由]
- [具体的な禁止行動3とその理由]

## 8. Responsive Behavior

- Mobile: ~[px]
- Tablet: [px] ~ [px]
- Desktop: [px]~
- Mobile-first: [yes/no]
- Touch targets: [px] 以上

主なレイアウト変化:
- [ブレークポイントでの変化1]
- [ブレークポイントでの変化2]

## 9. Agent Prompt Guide

**クイックカラーリファレンス:**
- Primary: [hex]
- Background: [hex]
- Text: [hex]

**推奨参照順序:**
1. Color Palette & Roles（色と用途の確認）
2. Component Stylings（コンポーネント実装時）
3. Typography Rules（テキスト実装時）
4. Layout Principles（レイアウト実装時）

**判断に迷ったとき:**
- 色: Color Palette の機能的役割欄を参照
- 間隔: Spacing Scale の倍数を使う
- 角丸: Component Stylings の記述値に統一
```

---

## 各セクションの記述ガイド

### 1. Visual Theme & Atmosphere
- ブランドの「雰囲気(vibe)」を自然言語で表現する
- キーワード: 温度感（暖かい/クール）、密度（情報密度高/低）、速度感（軽快/重厚）、年代感
- スクリーンショットや実サイトを見て感じた印象を言語化する
- 例: "Clean, minimal, with confident use of whitespace. Technical precision balanced with approachability."

### 2. Color Palette & Roles
- セマンティック名は「風情のある自然言語」で（"Deep Ocean" "Cloud White" など）
- 必ず hex 値を括弧内に含める
- 機能的役割は「何に使うか」を具体的に書く
- Primary/Secondary/Semantic/Neutrals の4グループに分類する

### 3. Typography Rules
- font-family はフォールバックチェーンを含める
- すべての階層（H1〜Caption）をテーブルで列挙する
- 用途欄には「どの画面・要素で使うか」を書く

### 4. Component Stylings
- 角丸: 技術値に加えて自然言語を必ず付ける（"sharp(0px)" "subtle(4px)" "rounded(8px)" "pill(9999px)"）
- 影: "ほのかな浮き" "浮き上がり強め" のような表現を付ける
- 各コンポーネントのインタラクション状態（hover/focus/disabled）を含める

### 5. Layout Principles
- 実際に使われているスペーシング値を列挙する
- コンテナ幅やグリッド設定は、コード（tailwind.config 等）から実値を引く

### 6. Depth & Elevation
- 影の段階は 4 段階以内に収める
- 各段階に用途（カード、モーダル等）を紐付ける

### 7. Do's and Don'ts
- VI PDF にある使用規定をそのまま反映できる場合が多い
- "Don't" には必ず理由を添える（可読性低下、ブランド毀損等）

### 8. Responsive Behavior
- ブレークポイントはコードから実値を引く
- タッチターゲットは 44px 以上が推奨（Apple HIG / WCAG 準拠）

### 9. Agent Prompt Guide
- エージェントが最初に参照すべき色をクイックリファレンスとして掲載する
- 「迷ったとき」のフォールバック判断を明記する
