# プロファイル管理

> 参照元: https://hermes-agent.nousresearch.com/docs/user-guide/profiles

プロファイルは `~/.hermes/` ディレクトリ全体（config.yaml, .env, SOUL.md, memories, skills, cron 等）を切り替える機構。仕事用 / 個人用 / 実験用などを完全分離して運用できる。

## CLI

```bash
hermes profile list                       # プロファイル一覧
hermes profile use <name>                 # デフォルトプロファイルに設定
hermes profile create <name>              # 新規作成（空のプロファイル）
hermes profile create <name> --clone work # 既存プロファイルから派生
hermes profile create <name> --clone-all  # config + 全データを複製
hermes profile show <name>                # プロファイル詳細
hermes profile rename <old> <new>
hermes profile delete <name>
hermes profile export <name> > work.tar   # アーカイブ化
hermes profile import work.tar
hermes profile alias <name>               # プロファイル専用ラッパー (`hermes-work` 等) を生成
```

## 一時的な切替

```bash
hermes --profile work chat                # コマンド単位で切替
hermes -p personal --tui
HERMES_PROFILE=work hermes                # 環境変数でも切替可能
```

## ストレージ

各プロファイルは `~/.hermes/profiles/<name>/` に独立したディレクトリを持つ。`default` プロファイルは互換のため `~/.hermes/` 直下に置かれる。

```
~/.hermes/
├── config.yaml          # default プロファイル
├── profiles/
│   ├── work/
│   │   ├── config.yaml
│   │   ├── .env
│   │   ├── SOUL.md
│   │   └── memories/
│   └── personal/
│       └── ...
```

## ユースケース

| シナリオ | プロファイル設計例 |
|---------|------------------|
| 業務と個人の API キー分離 | `work`（社内 OpenRouter キー）/ `personal`（個人 Anthropic） |
| プロバイダー比較実験 | `bench-anthropic`, `bench-openai`, `bench-deepseek` を `--clone` で派生 |
| クライアント別切替 | `client-a`, `client-b` で SOUL.md / メモリを分離 |
| Gateway 別運用 | `gateway-tg`（Telegram 用）/ `gateway-discord`（Discord 用） |

## エイリアス

```bash
hermes profile alias work                 # ラッパースクリプト hermes-work を作成
hermes-work chat -q "今日のタスクを整理"
```

ラッパーは `~/.hermes/bin/hermes-<name>` に配置され、`PATH` に自動追加される。
