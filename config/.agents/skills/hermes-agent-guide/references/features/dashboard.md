# Web ダッシュボード・ダッシュボードプラグイン

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard / dashboard-plugins

## 起動

```bash
pip install "hermes-agent[web]"        # 初回のみ
hermes dashboard                        # http://localhost:8645 で起動
hermes dashboard --port 9000           # ポート変更
hermes dashboard --host 0.0.0.0        # LAN に公開
```

## ページ構成

| ページ | 用途 |
|--------|------|
| Status | 起動状態・接続中 Gateway・現在のモデル |
| Config | `config.yaml` をブラウザから編集 |
| API Keys | `.env` の API キー管理（マスク表示） |
| Sessions | セッション一覧・検索・続行 |
| Logs | リアルタイムログ・エラー絞り込み |
| Analytics | トークン使用量・コスト・ツール頻度 |
| Cron | スケジュールタスクの管理 |
| Skills | インストール済みスキル管理 |

REST API も同一ポートで提供（`/api/*`）。`API_SERVER_KEY` で Bearer 認証可能。

## v0.11.0 ダッシュボード強化

- **i18n** — 英語 + 中国語
- **react-router レイアウト** — サイドバー + ルーティング刷新
- **モバイルレスポンシブ** — スマホ/タブレット対応
- **Vercel デプロイ対応** — 静的アセットを Vercel にホスト可能
- **per-session API call tracking** — セッション単位のリクエスト数・レイテンシ
- **One-click update + gateway restart** — UI からアップデートと再起動

## ライブテーマシステム

色・フォント・レイアウト・密度をテーマで一括制御。再読込なしでホットスワップ。CLI/TUI と同じテーマ規律を web に拡張。

```yaml
dashboard:
  theme: "dark-cozy"                   # 内蔵 / カスタム
  themes_dir: "~/.hermes/dashboard-themes"
```

## ダッシュボードプラグイン (v0.11.0)

サードパーティプラグインがダッシュボードに**カスタムタブ・ウィジェット・ビュー**を追加できる。フォーク不要。

### プラグイン側 API

```python
from hermes.plugin import HermesPlugin, register
from hermes.dashboard import DashboardTab

@register
class CostBreakdownTab(HermesPlugin):
    name = "cost-breakdown"

    def dashboard_tabs(self):
        return [
            DashboardTab(
                slug="cost",
                label="Cost",
                icon="dollar",
                component_path="cost_tab.tsx",   # プラグイン同梱の React コンポーネント
            )
        ]
```

`~/.hermes/plugins/<plugin>/dashboard/` 以下の TSX/JSX が自動でビルドされて配信される。

### 設定

```yaml
dashboard:
  enabled_plugins: [cost-breakdown, my-internal-metrics]
  disabled_plugins: []
```

## REST API 主要エンドポイント

| パス | 用途 |
|------|------|
| `/api/status` | 状態取得 |
| `/api/sessions` | セッション CRUD |
| `/api/cron` | Cron 操作 |
| `/api/usage` | 使用統計 |
| `/api/themes` | テーマ一覧・切替 |
| `/api/plugins/dashboard` | ダッシュボードプラグイン一覧 |
