# Slack

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/slack

## セットアップ

1. [Slack API](https://api.slack.com/apps) でアプリ作成
2. Socket Mode を有効化（推奨）
3. Event Subscriptions でイベント登録
4. OAuth & Permissions でスコープ設定
5. ワークスペースにインストール

## Socket Mode (推奨)

Basic Information → App-Level Tokens で `connections:write` スコープのトークン生成。Socket Mode を有効化すると Webhook URL 不要で動作する。

## 必要な Event Subscriptions

**Bot Events:**

- `message.channels` / `message.groups` / `message.im` / `message.mpim`
- `app_mention`

## 必要な Bot Token Scopes

- `chat:write` / `chat:write.customize`
- `channels:history` / `groups:history` / `im:history` / `mpim:history`
- `channels:read` / `groups:read` / `im:read`
- `reactions:write` / `reactions:read`
- `files:read` / `files:write`
- `users:read`

## 環境変数

| 変数 | 説明 |
|------|------|
| `SLACK_BOT_TOKEN` | `xoxb-` で始まる Bot User OAuth Token |
| `SLACK_APP_TOKEN` | `xapp-` で始まる App-Level Token (Socket Mode) |
| `SLACK_ALLOWED_USERS` | アクセス許可するユーザー ID（カンマ区切り） |

## config.yaml 設定

```yaml
platforms:
  slack:
    enabled: true
    socket_mode: true           # Socket Mode 使用（推奨）
    home_channel: ""            # 通知・cron 出力の送信先チャネル ID
    messages_tab: true          # App Home の Messages タブ有効化
    thread_behavior: "always"   # always: 常にスレッド返信 / auto: 状況判断
    multi_workspace: false      # 複数ワークスペース対応
    per_channel_prompts:
      "C0123456789": "このチャネル専用の指示"
```

## Messages タブ

Slack アプリ設定の App Home で "Messages Tab" を有効化すると、ボットとの DM が可能になる。`Allow users to send Slash commands and messages from the messages tab` にチェック。

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| 接続できない | Socket Mode の `SLACK_APP_TOKEN` が正しいか確認 |
| メッセージを受信しない | Event Subscriptions のイベント登録を確認 |
| `not_in_channel` エラー | ボットをチャネルに招待: `/invite @botname` |
| スレッド外で返信してしまう | `thread_behavior: "always"` を設定 |
| ファイルを読めない | `files:read` スコープを確認 |
| 複数ワークスペースで使いたい | `multi_workspace: true` + Org-wide install |
