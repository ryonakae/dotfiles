# その他のプラットフォーム

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu / https://hermes-agent.nousresearch.com/docs/user-guide/messaging/wecom / https://hermes-agent.nousresearch.com/docs/user-guide/messaging/bluebubbles / https://hermes-agent.nousresearch.com/docs/user-guide/messaging/qqbot

以下のプラットフォームも対応。詳細は `hermes setup` のインタラクティブウィザード参照。

| プラットフォーム | 接続方式 | 主要環境変数 | 備考 |
|----------------|---------|-------------|------|
| Feishu / Lark (飞书) | Event Subscription | `FEISHU_APP_ID`, `FEISHU_APP_SECRET` | Lark 国際版も同一設定 |
| WeCom (企业微信) | Bot API | `WECOM_CORP_ID`, `WECOM_AGENT_ID`, `WECOM_SECRET` | 企業向け WeChat |
| WeCom Callback | Callback API | `WECOM_CALLBACK_TOKEN`, `WECOM_CALLBACK_AES_KEY` | イベント受信用 |
| Weixin (微信) | WeChaty Bridge | `WEIXIN_TOKEN` | WeChaty ブリッジ経由 |
| BlueBubbles | REST API | `BLUEBUBBLES_URL`, `BLUEBUBBLES_PASSWORD` | macOS iMessage ブリッジ |
| QQ Bot | Official API | `QQ_APP_ID`, `QQ_TOKEN` | QQ 公式 Bot API |

## 共通パターン

すべてのプラットフォームで共通する設定項目:

```yaml
platforms:
  <platform>:
    enabled: true/false
    home_channel: ""            # 通知・cron 送信先
    per_channel_prompts: {}     # チャネル別プロンプト
```
