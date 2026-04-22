# Discord

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord

## セットアップ

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーション作成
2. Bot セクションでトークン生成
3. OAuth2 → URL Generator で招待 URL を作成
4. サーバーにボットを招待
5. `.env` にトークンを設定

## 必要な Intents

Developer Portal の Bot 設定で以下を有効化:

- **Message Content Intent** (必須)
- **Server Members Intent** (ロールベースアクセス使用時)
- **Presence Intent** (オプション)

## 必要な Permissions

招待 URL 生成時に以下を選択:

- `Send Messages` / `Send Messages in Threads`
- `Read Message History`
- `Manage Threads` (auto-thread 使用時)
- `Add Reactions` (リアクション使用時)
- `Manage Messages` (オプション)
- `Use Slash Commands`
- `Connect` / `Speak` (ボイスチャネル使用時)

## 環境変数

| 変数 | 説明 |
|------|------|
| `DISCORD_BOT_TOKEN` | Developer Portal から取得したトークン |
| `DISCORD_ALLOWED_USERS` | アクセス許可するユーザー ID（カンマ区切り） |
| `DISCORD_ALLOWED_ROLES` | アクセス許可するロール ID（カンマ区切り） |

## config.yaml 設定

```yaml
platforms:
  discord:
    enabled: true
    auto_thread: true           # 各メッセージに自動でスレッド作成
    home_channel: ""            # 通知・cron 出力の送信先チャネル ID
    reactions:
      thinking: "🤔"
      done: "✅"
      error: "❌"
    forum_channels:             # フォーラムチャネルでの自動スレッド
      enabled: false
      default_tags: []
    per_channel_prompts:
      "1234567890": "English only in this channel"
    slash_commands:              # ネイティブスラッシュコマンド
      enabled: true
      sync_on_start: true       # 起動時にコマンド同期
    voice:
      enabled: false
      tts_provider: "elevenlabs" # 音声合成プロバイダー
      stt_provider: "whisper"    # 音声認識プロバイダー
      auto_join: false           # ユーザー参加時に自動 join
```

## 招待 URL 生成

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=534723950656&scope=bot%20applications.commands
```

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| ボットがオンラインにならない | `DISCORD_BOT_TOKEN` を確認。Developer Portal でトークンをリセット |
| メッセージに反応しない | Message Content Intent が有効か確認 |
| スラッシュコマンドが表示されない | `slash_commands.sync_on_start: true` を確認。反映に最大1時間かかる場合がある |
| `Missing Permissions` エラー | ボットのロール順位がチャネル権限より上か確認 |
| スレッドが作成されない | `Manage Threads` 権限を確認 |
| ボイスに参加できない | `Connect` + `Speak` 権限を確認。`voice.enabled: true` を設定 |
