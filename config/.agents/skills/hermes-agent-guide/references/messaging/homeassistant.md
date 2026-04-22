# Home Assistant

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/homeassistant

Home Assistant と REST API / WebSocket で接続し、スマートホームデバイスを制御する。

## 環境変数

| 変数 | 説明 |
|------|------|
| `HASS_TOKEN` | Long-Lived Access Token |
| `HASS_URL` | Home Assistant の URL（例: `http://homeassistant.local:8123`） |

## ツール

| ツール | 説明 |
|--------|------|
| `ha_list_entities` | エンティティ一覧取得 |
| `ha_get_state` | エンティティの現在状態取得 |
| `ha_list_services` | 利用可能なサービス一覧 |
| `ha_call_service` | サービス呼び出し（照明 ON/OFF 等） |

## config.yaml 設定

```yaml
platforms:
  homeassistant:
    enabled: true
    watch_domains:               # 監視するドメイン
      - light
      - switch
      - climate
    watch_entities:              # 個別エンティティ監視
      - sensor.temperature
    ignore_entities:             # 無視するエンティティ
      - sensor.uptime
    cooldown_seconds: 30         # イベント通知のクールダウン
```

## セキュリティ

`shell_command` 等の危険なサービスドメインは自動的にブロックされる。WebSocket 経由でリアルタイムイベントを受信可能。
