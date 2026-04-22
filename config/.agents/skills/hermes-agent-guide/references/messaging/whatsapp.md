# WhatsApp

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/whatsapp

## セットアップ (Baileys ブリッジ)

Hermes Agent は [Baileys](https://github.com/WhiskeySockets/Baileys) ベースのブリッジ経由で WhatsApp に接続する。公式 API ではなく個人アカウントのセッションを利用する。

1. `config.yaml` で WhatsApp を有効化
2. Gateway 起動時に QR コードが表示される
3. WhatsApp アプリで QR をスキャンしてペアリング
4. セッション情報は自動保存される

## 環境変数

| 変数 | 説明 |
|------|------|
| `WHATSAPP_ALLOWED_USERS` | アクセス許可する電話番号（国コード付き、カンマ区切り） |

## config.yaml 設定

```yaml
platforms:
  whatsapp:
    enabled: true
    mode: "bot"                 # bot: 他ユーザーからの DM に応答 / self: 自分との会話 (Note to Self)
    session_persistence: true   # セッション情報を永続化
    home_channel: ""            # 通知送信先の電話番号または JID
```

## ペアリング方式

- **QR コード**: ターミナルに表示される QR をスキャン
- **ペアリングコード**: `hermes pairing whatsapp` で数字コードを生成、WhatsApp アプリで入力

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| QR がスキャンできない | ターミナルの文字サイズを小さくする。または `hermes pairing whatsapp` でコードペアリング |
| セッションが切れる | WhatsApp アプリの「リンク済みデバイス」で既存セッションを削除し再ペアリング |
| `Connection Closed` 頻発 | WhatsApp のアップデートによる非互換。`hermes update` で最新版に更新 |
| self モードで動かない | `mode: "self"` を設定し、自分宛のメッセージを送信 |
