# スキルシステム

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

## プログレッシブディスクロージャー

```
Level 0: skills_list()           → [{name, description}, ...]  (~3k tokens)
Level 1: skill_view(name)        → フルコンテンツ + メタデータ
Level 2: skill_view(name, path)  → 特定参照ファイル
```

## SKILL.md フォーマット

```yaml
---
name: my-skill
description: スキルの説明
version: 1.0.0
platforms: [macos, linux]     # オプション
environments: [kanban, docker, s6]   # relevance gate（v0.16.0）
metadata:
  hermes:
    tags: [python]
    category: devops
    fallback_for_toolsets: [web]    # Web ツール未利用時のみ表示
    requires_toolsets: [terminal]   # terminal 必須
    config:
      - key: my.setting
        description: "設定の説明"
        default: "value"
---
```

### `environments:` relevance gate（v0.16.0）

特定の環境（kanban / docker / s6 等）でのみスキルを active にする gate。bundled スキル軽量化の一環。

## スキルの管理（skill_manage ツール）

| アクション | 用途 |
|----------|------|
| `create` | 新規作成 |
| `patch` | 部分修正（推奨） |
| `edit` | 全体書き換え |
| `delete` | 削除 |
| `write_file` | 付属ファイル追加 |
| `remove_file` | 付属ファイル削除 |

## スキルハブ

```bash
hermes skills browse                              # 閲覧
hermes skills search kubernetes                   # 検索
hermes skills install openai/skills/k8s           # インストール
hermes skills install official/security/1password  # 公式オプション
hermes skills install https://example.com/...     # 直接 URL（v0.12.0）
```

ソース: `official`, `skills-sh`, `well-known`, `github`, `clawhub`, `lobehub`, `claude-marketplace`

trusted tap（自動信頼される source）:
- `OpenAI/skills`
- `anthropic/skills`
- `huggingface/skills`（v0.14.0）
- `NVIDIA/skills`（v0.16.0）

`skills.sh` カタログ取得は v0.15.1 で 858 → 19,932 エントリ（sitemap walk へ移行）。

## スキルバンドル / 同時ロード（v0.15.0）

`/<bundle-name>` で複数スキルを同時ロード可能。

## v0.16.0 で bundled から削除されたスキル

- `spotify`（→ native plugin の 7 tools）
- `linear`（→ `hermes mcp install linear`）
- `kanban-codex-lane`
- `debugging-hermes-tui-commands`
- 空カテゴリマーカー

## bundled → optional に降格（v0.16.0）

`baoyu-article-illustrator`, `baoyu-comic`, `creative-ideation`, `pixel-art`, `dspy`, `subagent-driven-development`, `minecraft-modpack-server`, `pokemon-player`, `hermes-s6-container-supervision`

## 統合されたスキル（v0.16.0）

- `webhook-subscriptions` + `native-mcp` → `hermes-agent` skill
- `writing-plans` → `plan` (v2.0.0)
