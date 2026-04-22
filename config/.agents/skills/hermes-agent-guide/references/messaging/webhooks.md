# Webhooks

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks

HTTP Webhook でイベント駆動のメッセージ受信に対応。GitHub、GitLab 等の各種サービスと連携可能。

## 環境変数

| 変数 | 説明 |
|------|------|
| `WEBHOOK_SECRET` | HMAC 署名検証用シークレット |

## config.yaml 設定

```yaml
platforms:
  webhooks:
    enabled: true
    routes:
      github_push:
        source: "github"
        events: ["push"]
        secret: "${WEBHOOK_SECRET}"
        prompt: "リポジトリ {repository.full_name} に push がありました: {head_commit.message}"
        deliver_to:
          - type: telegram
            chat_id: "-100123456789"
      gitlab_mr:
        source: "gitlab"
        events: ["merge_request"]
        deliver_to:
          - type: discord
            channel_id: "1234567890"
```

## 署名検証

GitHub (`X-Hub-Signature-256`)、GitLab (`X-Gitlab-Token`)、汎用 HMAC に対応。

## 機能

- プロンプトテンプレートで `{dot.notation}` によるペイロード参照
- 配信先: `github_comment`, `telegram`, `discord`, `slack` 等
- `hermes webhook subscribe` による動的サブスクリプション追加
- レート制限: 30 リクエスト/分
- 冪等キャッシュ: 1 時間（重複配信防止）
