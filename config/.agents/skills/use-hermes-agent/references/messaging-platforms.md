# Hermes Agent メッセージングプラットフォーム リファレンス

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/
> 対応バージョン: v0.16.0（23 プラットフォーム）

## 概要

Hermes Agent は `hermes gateway` コマンドでメッセージングプラットフォームと接続する。各プラットフォームは `.env` の API キーと `config.yaml` の設定で構成される。

各プラットフォームの詳細なセットアップ手順・設定・トラブルシューティングは `messaging/` 配下の個別ファイルを参照。

## プラットフォーム一覧（23 種）

| プラットフォーム | 参照先 | 接続方式 | 追加バージョン |
|----------------|--------|---------|---------------|
| Telegram | [messaging/telegram.md](messaging/telegram.md) | Bot API (ポーリング / Webhook) | 〜 |
| Discord | [messaging/discord.md](messaging/discord.md) | Bot Token + Gateway | 〜 |
| Slack | [messaging/slack.md](messaging/slack.md) | Socket Mode / Events API | 〜 |
| WhatsApp | [messaging/whatsapp.md](messaging/whatsapp.md) | Baileys ブリッジ (QR ペアリング) | 〜 |
| Signal | [messaging/signal.md](messaging/signal.md) | signal-cli REST API | 〜 |
| Email | [messaging/email.md](messaging/email.md) | IMAP/SMTP | 〜 |
| SMS | [messaging/sms.md](messaging/sms.md) | Twilio API + Webhook | 〜 |
| Home Assistant | [messaging/homeassistant.md](messaging/homeassistant.md) | REST API / WebSocket | 〜 |
| Matrix | [messaging/matrix.md](messaging/matrix.md) | mautrix SDK (E2EE 対応) | 〜 |
| Mattermost | [messaging/mattermost.md](messaging/mattermost.md) | Bot API + Personal Access Token | 〜 |
| Webhooks | [messaging/webhooks.md](messaging/webhooks.md) | HTTP Webhook (GitHub, GitLab 等) | 〜 |
| DingTalk | [messaging/dingtalk.md](messaging/dingtalk.md) | Stream Mode (WebSocket) | 〜 |
| Open WebUI | [messaging/open-webui.md](messaging/open-webui.md) | Chat Completions API / Responses API | 〜 |
| QQ Bot | [messaging/other-platforms.md](messaging/other-platforms.md) | QQ Official API v2 | v0.11.0 (17 番目) |
| Feishu / WeCom / Weixin / BlueBubbles | [messaging/other-platforms.md](messaging/other-platforms.md) | 中華圏向け / iMessage ブリッジ | 〜 |
| Microsoft Teams | [messaging/teams.md](messaging/teams.md) | Microsoft Graph API + Webhook | v0.12.0 (18 番目、初期はプラグイン)、v0.14.0 で end-to-end |
| Tencent 元宝（Yuanbao） | [messaging/yuanbao.md](messaging/yuanbao.md) | native adapter | v0.12.0 (19 番目) |
| Google Chat | [messaging/google-chat.md](messaging/google-chat.md) | Google Workspace API + Webhook | v0.13.0 (20 番目) |
| LINE | [messaging/line.md](messaging/line.md) | LINE Messaging API | v0.14.0 (21 番目) |
| SimpleX Chat | [messaging/simplex.md](messaging/simplex.md) | SimpleX CLI / WebSocket | v0.14.0 (22 番目) |
| ntfy | [messaging/ntfy.md](messaging/ntfy.md) | ntfy.sh HTTP (push 通知、アカウント不要) | v0.15.0 (23 番目、プラグイン) |

> **注**: Discord と Mattermost は v0.15.0 から bundled plugin に移行（コアからは分離されたが標準で利用可能）。

## 共通パターン

すべてのプラットフォームで共通する設定項目:

```yaml
platforms:
  <platform>:
    enabled: true/false
    home_channel: ""            # 通知・cron 送信先
    per_channel_prompts: {}     # チャネル別プロンプト
    allowed_channels: []        # アクセス制御（v0.13.0+）
    allowed_chats: []           # Telegram 等のグループ allowlist
    allowed_rooms: []           # Matrix 等
    gateway_restart_notification: true  # gateway 再起動通知（v0.13.0）
    busy_ack_enabled: true      # ack メッセージ（v0.13.0）
```

## 共通コマンド

```bash
hermes gateway start             # 全有効プラットフォームを起動
hermes gateway start telegram    # 特定プラットフォームのみ
hermes gateway stop
hermes gateway status
hermes gateway list              # クロスプロファイル status（v0.13.0）
hermes gateway logs
hermes send <platform> <target>  # スクリプト出力 pipe（v0.15.0）
```

## v0.13.0+ の共通拡張

- **`env_enablement_fn` / `cron_deliver_env_var`** — プラットフォームプラグインフック（IRC / Teams 等が移行）
- **メディア parity** — Telegram/Discord/Slack/Mattermost/Email/Signal で multi-image 送信 + 中央集約 audio routing + FLAC + Telegram document fallback
- **`[[as_document]]`** — スキルメディアルーティングディレクティブ
- **streaming defaults**（v0.16.0）— Telegram on / Discord off など per-platform
