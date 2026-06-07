# MCP (Model Context Protocol)

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp

ツール名規則: `mcp_<server_name>_<tool_name>`

## stdio サーバー

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
```

## HTTP サーバー

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"
```

## SSE サーバー（v0.13.0+）

```yaml
mcp_servers:
  events_api:
    url: "https://mcp.example.com/sse"
    transport: sse
    oauth_forward: true     # 既存 OAuth を SSE にも forward
```

## mTLS（HTTP / SSE、v0.15.0+）

```yaml
mcp_servers:
  secure_api:
    url: "https://mcp.example.com/mcp"
    tls:
      client_cert: /path/to/client.crt
      client_key: /path/to/client.key
      ca_bundle: /path/to/ca.pem
```

## フィルタリング

```yaml
tools:
  include: [create_issue, list_issues]   # ホワイトリスト
  exclude: [delete_customer]             # ブラックリスト
  resources: false                       # ユーティリティ無効化
  prompts: false
```

## Hermes を MCP サーバーとして実行

```bash
hermes mcp serve
```

10個のツールを公開: `conversations_list`, `messages_read`, `messages_send` 等

## Nous-approved MCP catalog（v0.15.0+）

```bash
hermes mcp                       # interactive picker
hermes mcp install linear        # 1-click install（v0.16.0 で linear などが optional 化）
```

- カタログから 1-click install
- registry-aware `mcp_` prefix
- Stdin paste-back fallback for headless OAuth
- `skip` at paste prompt（auth bypass せず disable）

## その他の改善

- **Stale-pipe retries**（v0.13.0、session-expired として再試行）
- **画像ツール結果を MEDIA tag として surface**（v0.13.0、dropping せず）
- **長時間 lifecycle wait に keepalive**（v0.13.0）
- **`supports_parallel_tool_calls`**、**Codex preset**（v0.14.0）
- **MCP bare command resolution under Docker** — `npx`/`npm`/`node` が `/usr/local/bin` に解決（v0.15.1）
- **false OAuth success 報告の修正**（v0.16.0）
- **初期 MCP 認証失敗での retry 停止**（v0.14.0）
- **Progressive tool disclosure** — MCP/plugin tools の scoped 開示（v0.16.0）
