# Hermes Agent メッセージングプラットフォーム リファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

## 概要

Hermes Agent は `hermes gateway` コマンドでメッセージングプラットフォームと接続する。各プラットフォームは `.env` の API キーと `config.yaml` の設定で構成される。

各プラットフォームの詳細なセットアップ手順・設定・トラブルシューティングは `messaging/` 配下の個別ファイルを参照。

## プラットフォーム一覧

| プラットフォーム | 参照先 | 接続方式 |
|----------------|--------|---------|
| Telegram | [messaging/telegram.md](messaging/telegram.md) | Bot API (ポーリング / Webhook) |
| Discord | [messaging/discord.md](messaging/discord.md) | Bot Token + Gateway |
| Slack | [messaging/slack.md](messaging/slack.md) | Socket Mode / Events API |
| WhatsApp | [messaging/whatsapp.md](messaging/whatsapp.md) | Baileys ブリッジ (QR ペアリング) |
| Signal | [messaging/signal.md](messaging/signal.md) | signal-cli REST API |
| Email | [messaging/email.md](messaging/email.md) | IMAP/SMTP |
| SMS | [messaging/sms.md](messaging/sms.md) | Twilio API + Webhook |
| Home Assistant | [messaging/homeassistant.md](messaging/homeassistant.md) | REST API / WebSocket |
| Matrix | [messaging/matrix.md](messaging/matrix.md) | mautrix SDK (E2EE 対応) |
| Mattermost | [messaging/mattermost.md](messaging/mattermost.md) | Bot API + Personal Access Token |
| Webhooks | [messaging/webhooks.md](messaging/webhooks.md) | HTTP Webhook (GitHub, GitLab 等) |
| DingTalk | [messaging/dingtalk.md](messaging/dingtalk.md) | Stream Mode (WebSocket) |
| Open WebUI | [messaging/open-webui.md](messaging/open-webui.md) | Chat Completions API / Responses API |
| その他 | [messaging/other-platforms.md](messaging/other-platforms.md) | Feishu, WeCom, Weixin, BlueBubbles, QQ Bot |

## 共通パターン

すべてのプラットフォームで共通する設定項目:

```yaml
platforms:
  <platform>:
    enabled: true/false
    home_channel: ""            # 通知・cron 送信先
    per_channel_prompts: {}     # チャネル別プロンプト
```

## 共通コマンド

```bash
hermes gateway start             # 全有効プラットフォームを起動
hermes gateway start telegram    # 特定プラットフォームのみ
hermes gateway stop
hermes gateway status
hermes gateway logs
```
