# SMS (Twilio)

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/sms

Twilio API 経由で SMS メッセージングに対応。Webhook でメッセージを受信する。

## 環境変数

| 変数 | 説明 |
|------|------|
| `TWILIO_ACCOUNT_SID` | Twilio アカウント SID |
| `TWILIO_AUTH_TOKEN` | Twilio 認証トークン |
| `TWILIO_PHONE_NUMBER` | Twilio の電話番号（`+1...` 形式） |

## セットアップ

1. Twilio コンソールで電話番号を取得
2. `.env` に認証情報を設定
3. Webhook URL を Twilio の Phone Number 設定に登録

## 制限事項

- メッセージ長上限: 1,600 文字（超過分は分割送信）
- 受信メッセージは Twilio のリクエスト署名で検証される
