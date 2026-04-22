# Matrix

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/matrix

mautrix SDK ベースで Matrix プロトコルに対応。E2EE（エンドツーエンド暗号化）もサポート。

## 環境変数

| 変数 | 説明 |
|------|------|
| `MATRIX_HOMESERVER` | ホームサーバー URL（例: `https://matrix.org`） |
| `MATRIX_USER_ID` | ボットのユーザー ID（`@bot:matrix.org` 形式） |
| `MATRIX_ACCESS_TOKEN` | アクセストークン（トークン認証の場合） |
| `MATRIX_PASSWORD` | パスワード（パスワード認証の場合） |
| `MATRIX_RECOVERY_KEY` | クロス署名用リカバリーキー（E2EE 時） |

## config.yaml 設定

```yaml
platforms:
  matrix:
    enabled: true
    e2ee: true                  # E2EE 有効化（libolm が必要）
    auto_thread: true           # スレッド自動作成
    mention_required: true      # メンション時のみ応答
    home_channel: ""
```

## E2EE サポート

- `libolm` ライブラリが必要
- `MATRIX_RECOVERY_KEY` でクロス署名の検証を自動化
- macOS では E2EE のプロキシモードが利用可能
- MSC3245 準拠のネイティブ音声メッセージに対応
