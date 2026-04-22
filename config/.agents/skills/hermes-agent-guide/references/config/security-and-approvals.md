# セキュリティ・承認モード・ブロックリスト

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#security

## セキュリティ設定

```yaml
security:
  redact_secrets: true
  tirith_enabled: true
  website_blocklist:
    enabled: false
    domains: []

approvals:
  mode: manual                  # manual | smart | off
```
