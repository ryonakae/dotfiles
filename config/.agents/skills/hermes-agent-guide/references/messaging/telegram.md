# Telegram

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram

## セットアップ

1. [@BotFather](https://t.me/BotFather) で `/newbot` → ボットトークンを取得
2. [@userinfobot](https://t.me/userinfobot) で自分のユーザー ID を取得
3. `.env` にトークンを設定
4. `config.yaml` でプラットフォーム設定

## 環境変数

| 変数 | 説明 |
|------|------|
| `TELEGRAM_BOT_TOKEN` | BotFather から取得したトークン |
| `TELEGRAM_ALLOWED_USERS` | アクセス許可するユーザー ID（カンマ区切り） |

## config.yaml 設定

```yaml
platforms:
  telegram:
    enabled: true
    webhook: false              # true: Webhook モード / false: ポーリング
    proxy: ""                   # SOCKS5/HTTP プロキシ URL
    privacy_mode: false         # true: グループで @ メンション時のみ応答
    home_channel: ""            # 通知・cron 出力の送信先チャット ID
    dns_fallback:
      enabled: false            # DNS 解決問題時の代替 DNS 使用
      servers: ["1.1.1.1"]
    reactions:
      thinking: "🤔"           # 処理中リアクション
      done: "✅"                # 完了リアクション
      error: "❌"               # エラーリアクション
    topics:
      dm:                       # DM でのトピック分離
        enabled: false
        auto_create: true       # トピック自動作成
      group_forum:              # グループフォーラムトピック
        enabled: false
        auto_create: true
    per_channel_prompts:        # チャネル別システムプロンプト
      "-100123456789": "このチャネルでは日本語で回答してください"
```

## Webhook モード

```yaml
platforms:
  telegram:
    webhook: true
    webhook_url: "https://yourdomain.com/telegram/webhook"
    webhook_port: 8443
```

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| ボットが応答しない | `TELEGRAM_BOT_TOKEN` を確認。BotFather で `/mybots` → API Token をリセット |
| グループで反応しない | `privacy_mode: false` に設定、または BotFather で Group Privacy を OFF |
| 接続タイムアウト | `proxy` または `dns_fallback` を設定。中国等の地域制限の可能性 |
| `Conflict: terminated by other getUpdates` | 同一トークンで複数インスタンスが起動している |
| Webhook 設定後にポーリングが動かない | `hermes gateway telegram reset-webhook` で Webhook を解除 |
