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
