# Google Chat 統合

> v0.13.0 で 20 番目のプラットフォームとして追加。

## 概要

Google Workspace の Google Chat と連携。スペース（旧 Room）と DM 対応。

## 前提条件

- Google Workspace アカウント（個人 Gmail では Chat API 制限あり）
- Google Cloud Project 作成、Chat API 有効化
- Service Account またはユーザー OAuth で認証

## セットアップ

### 1. Google Cloud Console

1. プロジェクト作成 → Chat API 有効化
2. Service Account 作成 → JSON キーダウンロード
3. Chat app（Bot）を Workspace に発行（Workspace 管理者権限が必要な場合あり）

### 2. `.env`

```bash
GOOGLE_CHAT_CREDENTIALS_FILE=/path/to/service-account.json
GOOGLE_CHAT_PROJECT_ID=...
GOOGLE_CHAT_BOT_NAME=hermes
```

### 3. `config.yaml`

```yaml
platforms:
  google_chat:
    enabled: true
    home_channel: "spaces/AAA..."
    allowed_channels:
      - "spaces/AAA..."
      - "users/USER_ID"
    streaming: false
```

### 4. Webhook 受信

Chat API は HTTPS webhook 経由でメッセージを受信。`hermes gateway setup google_chat` でウィザード起動。

## アクセス制御

- `allowed_channels` で space / DM allowlist
- Service Account を最小権限の Workspace スコープに絞る

## 関連メモ

- v0.13.0 で導入された `env_enablement_fn` / `cron_deliver_env_var` プラットフォームプラグインフックを使った汎用設計（IRC, Teams も同じ仕組み）
- メッセージ format は Google Chat の Card v2 を一部サポート
