# Web ダッシュボード・ダッシュボードプラグイン

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard / dashboard-plugins

## 起動

```bash
pip install "hermes-agent[web]"        # 初回のみ
hermes dashboard                        # http://localhost:8645 で起動
hermes dashboard --port 9000           # ポート変更
hermes dashboard --host 0.0.0.0        # LAN に公開
```

## ページ構成（v0.16.0 で完全管理パネル化）

| ページ | 用途 |
|--------|------|
| Status | 起動状態・接続中 Gateway・現在のモデル |
| Config | `config.yaml` をブラウザから編集 |
| API Keys / Credentials | `.env` の API キー管理（マスク表示） |
| Sessions | セッション一覧・検索・続行・bulk 操作（v0.16.0）・schedule picker |
| Logs | リアルタイムログ・エラー絞り込み |
| Analytics | トークン使用量・コスト・ツール頻度・per-model（v0.12.0）・hide フラグ（v0.14.0） |
| Cron | スケジュールタスクの管理 + modals（v0.14.0） |
| Skills | インストール済みスキル管理（lazy-fetch、v0.15.0） |
| Models | 全プロバイダ × モデル分析、main/auxiliary 切替（v0.12.0） |
| Plugins | プラグイン管理（v0.13.0） |
| Profiles | プロファイル管理ページ（v0.13.0、v0.16.0 で強化） |
| MCP Catalog | MCP サーバーの追加 / カタログ閲覧（v0.16.0） |
| Channels | メッセージング channel 管理（v0.16.0） |
| Webhooks / Hooks | webhook / hook 作成（v0.16.0） |
| Memory | memory 設定（v0.16.0） |
| Gateway | gateway 制御（v0.16.0） |
| System | システム情報（v0.16.0） |

REST API も同一ポートで提供（`/api/*`）。`API_SERVER_KEY` で Bearer 認証可能。

## v0.16.0 ダッシュボード強化

- **完全管理パネル化** — MCP Catalog / Channels / Credentials / Webhooks / Memory / Gateway / Hooks / System
- **Pluggable username/password login** — `register dashboard register` で self-hosted OAuth client 登録、generic OIDC provider 対応
- **Refresh-token rotation**
- **embedded chat 常時有効化** — `--tui` flag 削除
- **nous-blue テーマ**、`default-large`（18px、v0.13.0）
- **`@nous-research/ui` 移行**（v0.15.0）、Collapsible sidebar、mobile polish
- **configurable terminal background via theme**
- **`X-Forwarded-Prefix` リバースプロキシ対応**（v0.13.0）
- **Docker dashboard `--insecure` は `HERMES_DASHBOARD_INSECURE=1` 明示 opt-in**（v0.15.1）
- **Langfuse 観測性プラグイン**（v0.12.0、修正は v0.15.1）

## リモート接続（v0.16.0）

```bash
hermes dashboard register      # self-hosted OAuth client 登録
```

Hermes Desktop からこの dashboard に OAuth or username/password でログイン可能。

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
