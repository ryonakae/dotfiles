# 開発ガイドライン

## 最重要プロトコル (絶対遵守)

- **言語規定**: 思考プロセス、ユーザーへのレスポンス、アーティファクト、コミットメッセージ、コード内のコメントは必ず日本語で行ってください。システムエラーやログの引用は原文のままにしてください

## Agent Skillsについて

### カテゴリ別スキル一覧

#### React Native / Expo

| スキル名 | 使用タイミング | 主な用途 |
|---------|---------------|---------|
| `/react-native-best-practices` | パフォーマンス問題を扱う時 | FPS改善、メモリリーク対策、再レンダリング最適化、Hermes最適化、ブリッジオーバーヘッド削減 |
| `/expo-building-ui` | UIを構築する時 | Expo Routerでの画面構築、スタイリング、コンポーネント、ナビゲーション、アニメーション、ネイティブタブ |
| `/expo-data-fetching` | データ取得を実装する時 | fetch API、axios、React Query、SWR、エラーハンドリング、キャッシュ戦略、オフライン対応 |
| `/expo-cicd-workflows` | CI/CDを設定する時 | EAS Workflowの作成・編集、ビルドパイプライン自動化、デプロイ自動化 |
| `/expo-deployment` | アプリをデプロイする時 | iOS App Store、Android Play Store、Webホスティング、API routesへのデプロイ |
| `/expo-tailwind-setup` | Tailwindをセットアップする時 | Tailwind CSS v4のExpoでのセットアップ、react-native-css、NativeWind v5 |
| `/expo-dev-client` | 開発ビルドを作る時 | 開発ビルドの作成、TestFlightでの配布、チーム共有 |
| `/expo-use-dom` | WebコードをNativeで使う時 | Expo DOMコンポーネントでWebコードをネイティブで実行、段階的移行 |
| `/expo-api-routes` | API Routesを作る時 | Expo Router + EAS HostingでのAPI Routes作成ガイドライン |
| `/expo-upgrading-expo` | Expo SDKをアップグレードする時 | Expo SDKバージョンアップ、依存関係の解決 |

#### Next.js

| スキル名 | 使用タイミング | 主な用途 |
|---------|---------------|---------|
| `/next-best-practices` | Next.jsコードを書く時 | ファイル規約、RSC境界、データパターン、非同期API、メタデータ、エラーハンドリング、ルートハンドラー、画像/フォント最適化、バンドリング |
| `/next-cache-components` | Next.js 16のキャッシュを使う時 | PPR、use cacheディレクティブ、cacheLife、cacheTag、updateTag |
| `/next-upgrade` | Next.jsをアップグレードする時 | 公式マイグレーションガイド、codemod適用 |

#### SwiftUI / iOS

| スキル名 | 使用タイミング | 主な用途 |
|---------|---------------|---------|
| `/swiftui-liquid-glass` | Liquid Glass UIを実装する時 | iOS 26+ Liquid Glass API採用、既存機能のリファクタ、正確性・パフォーマンス・デザイン整合性のレビュー |
| `/swiftui-performance-audit` | SwiftUIパフォーマンス問題がある時 | レンダリング遅延、スクロールのカク付き、高CPU/メモリ使用、過剰なView更新、レイアウトスラッシュの診断と改善 |
| `/swiftui-ui-patterns` | SwiftUI UIを作成/リファクタする時 | ベストプラクティス、TabViewでのタブ設計、画面構成、コンポーネント固有パターンと実例 |
| `/swiftui-view-refactor` | SwiftUI Viewをクリーンアップする時 | 構造の整理、依存性注入、Observation使用、ViewModelの安全な扱い、@Observable状態の標準化 |
| `/swift-concurrency-expert` | Swift並行性の問題を扱う時 | Swift 6.2+並行性レビュー、コンプライアンス改善、コンパイラエラー修正 |

#### UI・データベース・その他

| スキル名 | 使用タイミング | 主な用途 |
|---------|---------------|---------|
| `/heroui-native` | HeroUI Nativeを使う時 | コンポーネント使用、インストール、テーマカスタマイズ、ドキュメント参照（Tailwind v4 via Uniwind） |
| `/supabase-postgres-best-practices` | Postgresクエリを扱う時 | クエリ最適化、スキーマ設計、データベース設定のパフォーマンス改善 |
| `/vercel-react-best-practices` | React/Next.jsのパフォーマンスを最適化する時 | Vercel Engineeringのベストプラクティス、コンポーネント最適化、データ取得、バンドル最適化 |
| `/frontend-design` | 高品質なフロントエンドUIを作る時 | Webコンポーネント、ページ、ダッシュボード、ランディングページのデザインとコード生成（汎用的なAI美学を避ける） |

### ユースケース別スキル対応表

#### パフォーマンス最適化
- React Native: `/react-native-best-practices`
- React/Next.js: `/vercel-react-best-practices`
- SwiftUI: `/swiftui-performance-audit`
- Postgres: `/supabase-postgres-best-practices`

#### UI/UX開発
- Expo Router: `/expo-building-ui`
- HeroUI Native: `/heroui-native`
- SwiftUI: `/swiftui-ui-patterns`, `/swiftui-liquid-glass`
- フロントエンド全般: `/frontend-design`

#### データ取得・API
- Expo: `/expo-data-fetching`, `/expo-api-routes`
- Next.js: `/next-best-practices`, `/next-cache-components`

#### デプロイ・CI/CD
- Expo: `/expo-deployment`, `/expo-cicd-workflows`
- 開発ビルド: `/expo-dev-client`

#### アップグレード・マイグレーション
- Expo SDK: `/expo-upgrading-expo`
- Next.js: `/next-upgrade`

#### コード品質・リファクタリング
- SwiftUI View: `/swiftui-view-refactor`
- Swift並行性: `/swift-concurrency-expert`

#### 特殊なユースケース
- Tailwindセットアップ: `/expo-tailwind-setup`
- WebコードのNative移行: `/expo-use-dom`
