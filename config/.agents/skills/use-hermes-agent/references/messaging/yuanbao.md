# Tencent 元宝（Yuanbao）統合

> v0.12.0 で 19 番目のプラットフォームとして追加（native adapter）。中国本土向け Tencent の AI チャットアプリ。

## 概要

Tencent 元宝（Yuanbao、腾讯元宝）の API を介してメッセージング統合。v0.16.0 で resolved media を `resourceId` キャッシュするようになった。

## 前提条件

- Tencent Tokenhub または元宝 Developer Platform 経由でクライアントトークン取得
- 中国本土 IP からのアクセス推奨（Tencent サービスは地域制限あり）

## `.env` 設定

```bash
YUANBAO_API_KEY=...
YUANBAO_APP_ID=...
YUANBAO_BOT_ID=...
```

## `config.yaml`

```yaml
platforms:
  yuanbao:
    enabled: true
    home_channel: ""
    allowed_chats: []
    streaming: false
```

## 関連プロバイダー

元宝と同時期に追加された Tencent 関連:
- **Tencent Tokenhub**（LLM プロバイダー、v0.12.0）
- Tencent 新モデル `tencent/hy3-preview`（v0.13.0）

## 注意事項

- Tencent サービスへのアクセスは中国本土向けに最適化されており、海外利用時は遅延が大きい
- メディア送信は v0.16.0 から `resourceId` ベースのキャッシュで重複アップロードを削減
