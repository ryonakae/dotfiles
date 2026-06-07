# Email (IMAP/SMTP)

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/email

## セットアップ

1. メールプロバイダーでアプリパスワードを生成（2FA 有効時は必須）
2. IMAP と SMTP の接続情報を `.env` に設定

## 環境変数

| 変数 | 説明 |
|------|------|
| `EMAIL_IMAP_HOST` | IMAP サーバー（例: `imap.gmail.com`） |
| `EMAIL_IMAP_PORT` | IMAP ポート（通常 `993`） |
| `EMAIL_SMTP_HOST` | SMTP サーバー（例: `smtp.gmail.com`） |
| `EMAIL_SMTP_PORT` | SMTP ポート（通常 `587`） |
| `EMAIL_ADDRESS` | メールアドレス |
| `EMAIL_PASSWORD` | パスワードまたはアプリパスワード |
| `EMAIL_ALLOWED_SENDERS` | 受信許可するアドレス（カンマ区切り） |

## config.yaml 設定

```yaml
platforms:
  email:
    enabled: true
    polling_interval: 60        # メール確認間隔（秒）
    skip_attachments: false     # 添付ファイルを無視
    imap_folder: "INBOX"        # 監視フォルダ
    mark_as_read: true          # 処理済みを既読にする
    home_channel: ""            # 通知送信先アドレス
```

## プロバイダー別設定

**Gmail:**
- 2FA を有効化 → アプリパスワードを生成（Google アカウント → セキュリティ → アプリパスワード）
- IMAP: `imap.gmail.com:993` / SMTP: `smtp.gmail.com:587`

**Outlook/Microsoft 365:**
- IMAP: `outlook.office365.com:993` / SMTP: `smtp.office365.com:587`
- OAuth を使う場合は `hermes auth email` でフローを実行

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| IMAP 認証エラー | アプリパスワードを使用しているか確認。Gmail は「安全性の低いアプリ」が廃止済み |
| メールを受信しない | `polling_interval` と `imap_folder` を確認 |
| 送信できない | SMTP ポートとホストを確認。587 (STARTTLS) または 465 (SSL) |
| 添付ファイル処理エラー | `skip_attachments: true` で回避可能 |
