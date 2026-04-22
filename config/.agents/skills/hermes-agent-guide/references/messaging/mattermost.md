# Mattermost

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/mattermost

Bot アカウント経由で Mattermost に接続。Personal Access Token で認証する。

## 環境変数

| 変数 | 説明 |
|------|------|
| `MATTERMOST_URL` | サーバー URL（例: `https://mattermost.example.com`） |
| `MATTERMOST_TOKEN` | Personal Access Token |

## config.yaml 設定

```yaml
platforms:
  mattermost:
    enabled: true
    reply_mode: "thread"         # off / thread
    free_response_channels:      # メンション不要で応答するチャネル
      - "town-square"
    per_channel_prompts:
      "channel-id": "チャネル固有のプロンプト"
    home_channel: ""
```

## セットアップ

1. Mattermost 管理画面で Bot アカウントを作成
2. Personal Access Token を生成
3. Bot をチャネルに招待
