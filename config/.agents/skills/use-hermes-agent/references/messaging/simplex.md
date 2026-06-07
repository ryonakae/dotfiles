# SimpleX Chat 統合

> v0.14.0 で 22 番目のプラットフォームとして追加。

## 概要

SimpleX Chat（identifier-free な P2P メッセンジャー）と連携。中央集中型のアカウントを持たず、双方向の鍵交換でセッションを確立する。プライバシー重視のユースケース向け。

## 前提条件

- SimpleX CLI または SimpleX Chat bot 実装をローカルで起動
- Hermes と SimpleX CLI を WebSocket または stdio 経由で接続

## セットアップ

### 1. SimpleX CLI を起動

```bash
# Linux/macOS（公式バイナリを配置）
simplex-chat -p 5225
```

ポート 5225 で WebSocket をリッスンする bot プロセスとして起動。

### 2. `.env`

```bash
SIMPLEX_WS_URL=ws://localhost:5225
SIMPLEX_DISPLAY_NAME=hermes
```

### 3. `config.yaml`

```yaml
platforms:
  simplex:
    enabled: true
    home_channel: ""              # 接続済み相手の contact ID
    allowed_chats: []
    streaming: false
```

### 4. 連絡先の確立

SimpleX は QR コードまたは一回限りリンクで連絡先を確立する。Hermes 起動後にユーザー側からリンクを通じて接続する。

## アクセス制御

- `allowed_chats` で contact ID allowlist
- SimpleX は中央サーバーがないため、`GATEWAY_ALLOWED_USERS` は不要だが、初回接続時に signing key で identity を pin することを推奨

## 注意事項

- SimpleX のプロトコル仕様は活発に更新されるため、互換性のあるバイナリバージョンを使う
- バンドル形式のメディア送信は限定的（v0.14.0 時点では text/image のみ）
