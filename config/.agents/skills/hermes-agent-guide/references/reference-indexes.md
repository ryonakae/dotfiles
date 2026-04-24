# 公式リファレンスインデックス

> 参照元: https://hermes-agent.nousresearch.com/docs/reference/

公式 docs `reference/` カテゴリの目次と、本スキル内対応 reference へのリンク。

## CLI 関連

| 公式ページ | 本スキル内対応 | 用途 |
|-----------|---------------|------|
| `reference/cli-commands` | `references/cli-commands.md` | `hermes <command>` 全サブコマンド |
| `reference/slash-commands` | `references/cli-commands.md` の「スラッシュコマンド」節 | セッション内 `/command` 一覧 |
| `reference/profile-commands` | `references/features/profiles.md` | `hermes profile` サブコマンド |

## 設定・環境変数

| 公式ページ | 本スキル内対応 | 用途 |
|-----------|---------------|------|
| `reference/environment-variables` | `references/environment-variables.md` | 全 env var 一覧（プロバイダー / Gateway / ツール） |
| `reference/mcp-config-reference` | `references/features/mcp.md` + `references/config/mcp-and-skills.md` | MCP サーバー設定の完全仕様 |

## ツール・スキル

| 公式ページ | 本スキル内対応 | 用途 |
|-----------|---------------|------|
| `reference/tools-reference` | `references/features/tools-and-toolsets.md` | 全 47 ツールの詳細仕様 |
| `reference/toolsets-reference` | `references/features/tools-and-toolsets.md` | 19 ツールセットの分類 |
| `reference/skills-catalog` | （対象外） | 公式バンドルスキルの一覧。`hermes skills browse` で実機参照を推奨 |
| `reference/optional-skills-catalog` | （対象外） | オプションスキル（red-teaming, blockchain 等）。同上 |

## トラブルシュート

| 公式ページ | 本スキル内対応 | 用途 |
|-----------|---------------|------|
| `reference/faq` | `references/troubleshooting.md` | FAQ・診断手順 |

## 検索のコツ

公式 docs サイト全体は Algolia 検索（DocSearch）が効く。本スキル内検索が空振りした場合は:

1. `references/troubleshooting.md` を最初に当たる
2. `references/environment-variables.md` で env 名を直接 grep
3. それでも見つからなければ公式 `reference/` カテゴリを直接参照

## 個別バンドルスキルの解説について

`bundled/apple/`, `bundled/creative/`, `bundled/mlops/` 等の個別スキル解説（50+ 本）は本ガイドのスコープ外。理由:

- スキルは `hermes skills browse` で常に最新版が見える
- 数が多くスキル本体が肥大化する
- 個別スキルの SKILL.md 自体が公式かつ正規ドキュメント

必要に応じて `hermes skills inspect <name>` で個別スキルの SKILL.md を直接読むこと。
