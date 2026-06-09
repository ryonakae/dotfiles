# DESIGN.md 記述例

## 使い方

- 実際の記述粒度と表現形式の参考として使う
- そのままコピーするのではなく、対象ブランドに合わせて調整する
- 各例の書き方パターン（名前 + hex + 役割）を自分のプロジェクトに適用する

---

## 例 1: SaaS プロダクト（ミニマル・プロフェッショナル系）

### Color Palette & Roles

**Primary**
- **Deep Ocean** (#1A73E8) — 主要ボタン、リンク、選択状態のアクセント
- **Pressed Ocean** (#1557B0) — Primary のホバー・クリック状態

**Semantic**
- **Fresh Mint** (#34A853) — 成功通知、完了バッジ、ポジティブな指標
- **Alert Crimson** (#EA4335) — エラーメッセージ、必須マーク、破壊的アクション
- **Warm Honey** (#FBBC04) — 警告バナー、注意アイコン、進行中の状態

**Neutrals & Surfaces**
- **Snow** (#FFFFFF) — カード背景、入力フィールド背景
- **Light Gray** (#F8F9FA) — ページ背景、セクション区切り
- **Divider Gray** (#E8EAED) — 区切り線、入力ボーダー
- **Charcoal** (#202124) — 見出し、本文メインテキスト
- **Slate** (#5F6368) — 補助テキスト、プレースホルダー
- **Disabled Text** (#BDBDBD) — 無効状態のテキスト・アイコン

### Typography Rules
- Font Family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
- Base Size: 16px

| Role      | Size | Weight | Line Height | Use                    |
|-----------|------|--------|-------------|------------------------|
| Heading 1 | 32px | 700    | 1.2         | ページタイトル          |
| Heading 2 | 24px | 600    | 1.3         | セクション見出し        |
| Heading 3 | 20px | 600    | 1.4         | カード見出し、サブセクション |
| Body      | 16px | 400    | 1.6         | 記事本文、説明文        |
| Small     | 14px | 400    | 1.5         | フォームラベル、メタ情報 |
| Caption   | 12px | 400    | 1.5         | タイムスタンプ、注記    |

### Component Stylings — Buttons
- **Primary**: 背景 Deep Ocean (#1A73E8)、文字 Snow (#FFFFFF)、角丸 やや丸み (8px)、影 ほのかな浮き (0 1px 2px rgba(0,0,0,0.1))
- **Secondary**: 背景 透明、文字 Deep Ocean (#1A73E8)、ボーダー 1px solid #1A73E8、角丸 やや丸み (8px)
- **Ghost**: 背景 透明、文字 Slate (#5F6368)、ボーダーなし、ホバー時背景 Light Gray (#F8F9FA)
- **Disabled**: 背景 Light Gray (#E8EAED)、文字 Disabled Text (#BDBDBD)、操作不可

### Depth & Elevation
- **Level 0 (Flat)**: 影なし — ページ背景、インラインテキスト
- **Level 1 (Subtle)**: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06) — カード、ドロップダウン
- **Level 2 (Medium)**: 0 4px 12px rgba(0,0,0,0.12) — モーダル、フローティングボタン
- **Level 3 (Strong)**: 0 8px 24px rgba(0,0,0,0.16) — ダイアログ、全画面オーバーレイ

---

## 例 2: EC / コマース系（暖かみ・信頼感）

### Visual Theme & Atmosphere
Warm, approachable, and trustworthy. Emphasizes product photography with generous whitespace. Brand communicates quality through restraint — avoiding visual clutter in favor of clear product hierarchy.

Key Characteristics:
- 温かみのある暖色系ニュートラルを基調
- 写真を引き立てる余白の活用
- アクションはシンプルに絞る（1画面1CTA）

### Color Palette & Roles
**Primary**
- **Terracotta** (#C4613D) — 購入CTA、主要アクション、プロモーションバナー
- **Deep Terracotta** (#A04D2F) — Primary ホバー状態

**Neutrals & Surfaces**
- **Warm White** (#FAFAF8) — ページ背景
- **Cream** (#F5F0EB) — セクション背景、カード背景
- **Warm Border** (#E8E0D8) — 区切り線
- **Espresso** (#2D1F17) — 本文テキスト、見出し
- **Taupe** (#7D6B5E) — 補助テキスト、価格の補足情報

### Do's and Don'ts

**Do**
- 商品画像は白または Warm White 背景に配置する
- CTA ボタンは Terracotta 色に統一し、1 画面に 1 つに絞る
- テキストのコントラスト比は WCAG AA（4.5:1）以上を維持する

**Don't**
- Terracotta を背景のベタ塗りに使わない（視覚的疲労の原因）
- 価格表示で 3 種類以上のフォントウェイトを使わない
- 商品カードに 2 種類以上のシャドウスタイルを混在させない

---

## 例 3: Color Palette の精密な記述パターン（推奨）

以下のパターンが最も情報密度が高く、エージェントが迷わない:

```
- **[風情ある自然言語名]** ([hex]) — [使う場所と状況], [補足的なニュアンス]
```

実例:
```
- **Midnight Indigo** (#1B1F3A) — 主要テキスト、見出し。ピュアブラックより柔らかく、可読性を確保しつつ高級感を演出
- **Glacier Blue** (#EBF4FF) — フォーム入力の背景、ホバー時のリスト行。アクティブ感を視覚的に示す
- **Ember** (#FF6B35) — 割引バッジ、限定ラベル等の緊急性・希少性を示すアクセント。週2回以上の使用は避ける
```

---

## 例 4: Layout Principles の記述パターン

```markdown
## 5. Layout Principles

- Base Spacing Unit: 8px
- Spacing Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96px
- Container Max Width: 1200px（コンテンツ）, 1440px（フルブリード）
- Grid: 12カラム、ガター 24px（モバイル: 16px）
- Whitespace Philosophy: コンテンツ間の余白は最小 24px、セクション間は最小 64px。余白は「空白」ではなく「呼吸」として機能させる
- Border Radius Scale: なし(0) / 微小(2px) / やや丸み(4px) / 丸み(8px) / 大きめ(16px) / ピル型(9999px)
```
