# DingTalk (钉钉)

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/dingtalk

Stream Mode（WebSocket）で接続。パブリック URL 不要で利用可能。

## 環境変数

| 変数 | 説明 |
|------|------|
| `DINGTALK_APP_KEY` | アプリケーション Client ID |
| `DINGTALK_APP_SECRET` | アプリケーション Client Secret |

## config.yaml 設定

```yaml
platforms:
  dingtalk:
    enabled: true
    home_channel: ""
```

## 機能

- Stream Mode により WebSocket 接続（外部 URL 不要）
- AI Card 対応（リッチメッセージ）
- 絵文字リアクション（処理中: 🤔 / 完了: 🥳）
- QR コードによるデバイスフローセットアップ
