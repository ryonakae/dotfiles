# MCP サーバー設定・スキル設定・外部ディレクトリ

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration#skill-settings / https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference

## MCP サーバー設定

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
    tools:
      include: [list_issues, create_issue]  # ホワイトリスト
      exclude: []                            # ブラックリスト
      resources: true                        # リソースユーティリティ
      prompts: true                          # プロンプトユーティリティ
    timeout: 30
    connect_timeout: 10
    enabled: true
    sampling:
      enabled: true
      max_tokens_cap: 4096
      timeout: 30
      max_rpm: 10

  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"
```

## スキル設定

```yaml
skills:
  external_dirs:                # 外部スキルディレクトリ
    - ~/.agents/skills
  config:                       # スキル個別設定
    myplugin:
      path: ~/myplugin-data
  disabled: []                  # グローバル無効化
  platform_disabled:
    telegram: [skill-a]         # プラットフォーム別無効化
```
