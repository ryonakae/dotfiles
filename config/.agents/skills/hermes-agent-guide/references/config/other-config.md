# その他の設定

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

## Quick コマンド

```yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
```

## 補助モデル

```yaml
auxiliary:
  vision:
    provider: "auto"
    model: ""
    timeout: 120
  web_extract:
    provider: "auto"
    timeout: 360
  compression:
    model: "google/gemini-3-flash-preview"
    timeout: 120
  approval:
    timeout: 30
  session_search:
    timeout: 30
```

## 委譲設定

```yaml
delegation:
  model: ""                     # サブエージェント用モデル
  provider: ""
  base_url: ""
  api_key: ""
```

## コード実行

```yaml
code_execution:
  mode: project                 # project | strict
  timeout: 300
  max_tool_calls: 50
```

## Web 検索バックエンド

```yaml
web:
  backend: firecrawl            # firecrawl | parallel | tavily | exa
```

## ブラウザ設定

```yaml
browser:
  inactivity_timeout: 120
  command_timeout: 30
  record_sessions: false
```

## タイムゾーン

```yaml
timezone: "Asia/Tokyo"          # IANA タイムゾーン
```

## 認証情報プール

```yaml
credential_pool_strategies:
  openrouter: round_robin       # fill_first | round_robin | least_used | random
  anthropic: least_used
```

## コンテキストファイル

| ファイル | 用途 | スコープ |
|---------|------|-------|
| `SOUL.md` | エージェントアイデンティティ | `~/.hermes/SOUL.md` |
| `.hermes.md` / `HERMES.md` | プロジェクト指示（最高優先） | git root まで探索 |
| `AGENTS.md` | プロジェクト指示 | CWD + サブディレクトリ再帰 |
| `CLAUDE.md` | Claude Code 互換 | CWD + サブディレクトリ |
| `.cursorrules` | Cursor IDE 互換 | CWD のみ |

優先順位: `.hermes.md` > `AGENTS.md` > `CLAUDE.md` > `.cursorrules`

## Git Worktree

```yaml
worktree: false                 # true=常に worktree 作成
```

## セッション管理

```yaml
group_sessions_per_user: true   # true=ユーザー別, false=チャット別
unauthorized_dm_behavior: pair  # pair | ignore
```
