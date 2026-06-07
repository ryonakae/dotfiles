# LINE Messaging API 統合

> v0.14.0 で 21 番目のプラットフォームとして追加。

## 概要

LINE Messaging API を介して個別チャット・グループチャットと連携。日本市場向けに重要。

## 前提条件

- LINE Developers アカウント
- Messaging API channel 作成 → Channel Access Token (long-lived) 取得
- Webhook URL（HTTPS）を Developers Console に登録

## `.env`

```bash
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

## `config.yaml`

```yaml
platforms:
  line:
    enabled: true
    home_channel: "<user-id-or-group-id>"
    webhook_url: https://your-host.example/line/webhook
    allowed_chats: []
    streaming: false
```

## アクセス制御

- LINE では `userId` / `groupId` / `roomId` を allowlist 化
- DM 利用時は LINE Official Account が「友だち追加」されている必要がある

## メディア対応

- LINE は画像・スタンプ・動画・音声・位置情報を transport できる
- 5MB を超えるメディアは LINE 側で content delivery URL を経由

## 関連メモ

- LINE は per-message rate limit が厳しいので、`hermes send` で大量送信する際は注意
- 中継 Webhook URL の HTTPS 化は必須（`pinggy-tunnel` スキル参照）
