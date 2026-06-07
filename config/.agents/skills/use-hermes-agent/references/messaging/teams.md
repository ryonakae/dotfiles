# Microsoft Teams 統合

> v0.12.0 で 18 番目のプラットフォームとして追加（初期はプラグイン経由）、v0.14.0 で end-to-end 統合（Graph auth + webhook listener + pipeline runtime + outbound delivery）。

## 概要

Microsoft Graph API を利用して Teams チャネル・1:1 チャット・グループチャットと連携。
outbound（hermes → Teams）と inbound（Teams → hermes、Webhook）の双方向対応。

## 前提条件

- Microsoft Entra ID（旧 Azure AD）テナント
- Bot Framework Registration または Azure App Registration（Application permissions: `ChannelMessage.Send`, `Chat.Read`, `Chat.ReadWrite`, etc.）
- Public HTTPS endpoint（webhook 受信）

## セットアップ

### 1. App Registration を作成

Azure Portal → Microsoft Entra ID → App registrations → 新規登録。
- Client ID, Tenant ID, Client Secret を取得
- API permissions に Microsoft Graph の Application permissions を付与（admin consent 必要）

### 2. `.env` に認証情報を設定

```bash
TEAMS_TENANT_ID=...
TEAMS_CLIENT_ID=...
TEAMS_CLIENT_SECRET=...
TEAMS_WEBHOOK_SECRET=...      # webhook validation 用
TEAMS_BOT_ID=...              # Bot Framework 経由の場合
```

### 3. `config.yaml`

```yaml
platforms:
  teams:
    enabled: true
    home_channel: "<team-id>/<channel-id>"
    webhook_url: https://your-host.example/teams/webhook
    allowed_channels:
      - "<team-id>/<channel-id>"
    streaming: false
```

### 4. Webhook 公開

```bash
hermes gateway setup teams
hermes gateway start teams
```

Pinggy / ngrok / Cloudflare Tunnel 等で webhook URL を公開する（`pinggy-tunnel` スキル参照）。

## アクセス制御

- `allowed_channels` で `<team-id>/<channel-id>` 形式の allowlist
- DM は `GATEWAY_ALLOWED_USERS` で UPN（user@tenant）を allowlist 化
- Application permission のスコープを最小限に絞る

## 関連メモ

- v0.14.0 で IRC + Teams が `env_enablement_fn` / `cron_deliver_env_var` プラットフォームプラグインフックに移行
- v0.12.0 時点ではプラグイン経由の MS Bot Framework 統合のみだった
