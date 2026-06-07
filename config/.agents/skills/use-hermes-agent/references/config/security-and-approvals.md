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

## Redaction（v0.12.0 / v0.13.0）

```yaml
redaction:
  enabled: true                  # v0.12.0 でデフォルト false → v0.13.0 で再び ON
  custom_patterns: []
```

v0.12.0 で patch 破損問題を回避するため一時的に OFF にされたが、v0.13.0 で 8 件の P0 セキュリティ修正の一環として再び ON。

## Prompt Caching（v0.12.0+）

```yaml
prompt_caching:
  cache_ttl: 5m                  # 5m | 1h（Claude 系のクロスセッション 1h は v0.14.0）
```

## 共通セキュリティ強化（v0.13.0〜v0.16.0）

- **TOCTOU 修正**: `auth.json` と MCP OAuth
- **SSRF floor 強制**: browser cloud-metadata（v0.13.0）、URL SSRF check を event loop 外（v0.16.0）
- **Cron prompt-injection scan**（v0.13.0）
- **`hermes debug share` 時の redaction**
- **MCP mTLS サポート**（v0.15.0）
- **Bedrock inference bearer token を subprocess env から strip**（v0.16.0）
- **`bws_cache.json` を file-safety read guard 対象に**（v0.16.0）
- **vetted skill content の invisible unicode を sanitize**（v0.16.0）
- **CVE-2026-48710 (Starlette BadHost) パッチ**（v0.16.0、Starlette ≥1.0.1 pin）
- **docker restart/stop/kill を `DANGEROUS_PATTERNS` に追加**（v0.16.0）
