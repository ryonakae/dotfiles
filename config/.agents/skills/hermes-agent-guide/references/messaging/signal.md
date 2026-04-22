# Signal

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/signal

## セットアップ (signal-cli)

1. [signal-cli](https://github.com/AsamK/signal-cli) をデーモンモードで起動
2. スマホの Signal アプリからデバイスをリンク
3. `.env` に設定

## 環境変数

| 変数 | 説明 |
|------|------|
| `SIGNAL_CLI_URL` | signal-cli REST API の URL（例: `http://localhost:8080`） |
| `SIGNAL_PHONE_NUMBER` | リンクした電話番号（`+81...` 形式） |
| `SIGNAL_ALLOWED_USERS` | アクセス許可する電話番号（カンマ区切り） |

## config.yaml 設定

```yaml
platforms:
  signal:
    enabled: true
    note_to_self: true          # Note to Self での会話を有効化
    group_access: false         # グループメッセージへの応答
    home_channel: ""            # 通知送信先
```

## デバイスリンク

```bash
# signal-cli でリンク URI を生成
signal-cli link -n "hermes-agent"
# 表示される URI を QR 化してスマホでスキャン
```

## トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| 接続できない | `SIGNAL_CLI_URL` と signal-cli デーモンの起動を確認 |
| メッセージが届かない | デバイスリンクが有効か Signal アプリで確認 |
| グループで応答しない | `group_access: true` を設定 |
