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
```

ソース: `official`, `skills-sh`, `well-known`, `github`, `clawhub`, `lobehub`, `claude-marketplace`
