# dotfiles

macOS 向け設定ファイル管理リポジトリ。`config/` 配下を `$HOME` にシンボリックリンクして展開する。新規マシンのセットアップ手順と Hermes Agent の運用詳細は `README.md` を参照。

## 編集の基本

- **`config/` 配下のファイルを直接編集する**（`$HOME` の symlink 先は編集しない）
- `config/<path>` が `~/<path>` にそのまま対応する。例:
  - `config/.config/fish/functions/dc.fish` → `~/.config/fish/functions/dc.fish`
  - `config/.claude/settings.json` → `~/.claude/settings.json`
- `*.example` パターン: マシン固有・機密を含むファイルは `.example` をリポジトリ管理し、実ファイルは `.gitignore` で除外（`brew/Brewfile`, `config/.config/fish/config.fish`, `~/.hermes/services/.env` など）
- 機密情報（API キー、トークン等）を `*.example` に含めない
- env 変数の置き場: マシン非依存の設計定数は wrapper（fish 関数 / shell スクリプト）に直書き、機密・マシン固有値は `.env`（実体は `.gitignore`）に分離する
- EditorConfig: スペース 2、LF、UTF-8

## scripts/

- `scripts/copy.sh` — `*.example` を実ファイルへコピー（既存はスキップ）
- `scripts/create-symlink.sh` — `config/` を `$HOME` に symlink（`.DS_Store`, `*.example`, `skills/` はスキップ）
- `scripts/create-skills-symlink.sh` — スキルを各エージェントの `skills/` 配下へ配布
- `scripts/remove-broken-symlinks.sh` — 壊れた symlink を対話的に削除（`-y` で自動）
- `scripts/install.sh` — Xcode CLI Tools と Homebrew（新規マシン向け、初回のみ）

## エージェント設定

```
config/
├── .agents/                    # 全エージェント共通（AGENTS.md、グローバルスキル、通知フック）
├── .claude/                    # Claude Code 固有（settings.json、フック、Claude 専用スキル）
├── .codex/                     # Codex 固有
├── .gemini/                    # Gemini CLI 固有
├── .hermes/                    # Hermes Agent 固有（SOUL.md、Docker compose）
└── .config/agent-safehouse/    # sandbox-exec ポリシー
```

- 共通指示書は `config/.agents/AGENTS.md`（言語・Python 実行・Web 検索ルール等）。`.claude/CLAUDE.md` と `.codex/AGENTS.md` から symlink されている。`.gemini/GEMINI.md` は別実体なので、共通ルール変更時は個別に同期する
- スキル配布: `config/.agents/skills/` がグローバル、`config/.claude/skills/` が Claude 専用。`create-skills-symlink.sh` が各エージェントの `skills/` ディレクトリへ symlink する
- エージェント CLI は fish 関数（`safe`, `claude`, `gemini`, `codex`, `hermes` など）経由で agent-safehouse サンドボックス内で起動する
- 共通 sandbox 引数は `config/.config/fish/functions/__safehouse_args.fish`
- 機密ファイルの deny ルールは `config/.config/agent-safehouse/local-overrides.sb`
- Hermes Agent 専用の deny ルールは `hermes-overrides.sb`（パーソナルディレクトリ・Library 遮断、他エージェント設定の write deny）
- **`hermes.fish` と `config/.config/agent-safehouse/safe-hermes-gateway.sh` の safehouse 引数は原則同期する**。ただし gateway は自律実行向けに `clipboard` / `cleanshot` など対話用 feature を意図的に省く場合がある。片方を変更したら、差分が意図したものか必ず確認する
- Hermes gateway の launchd 操作は `hermes-gateway {start|stop|restart|status}` に統一する（`bootout` / `bootstrap` 直叩きはしない）

## Hermes Agent 固有メモ

運用・セットアップ・トラブルシュートは `README.md` の「Hermes Agent」節を参照。

- dotfiles で管理するのは 5 ファイルのみ: `SOUL.md`, `services/docker-compose.yml`, `services/.env.example`, `services/hindsight/config.json`, `services/hindsight/.env.example`
- 管理対象外: `config.yaml`（クレデンシャル）、`hooks/` / `cron/` / `automations/` / `skills/hermes-custom/`（自己改善で書き換わる）、memory / session / 認証系全般
- `hermes gateway install --force` / `start` / `setup` の一部分岐は plist を再生成するため、実行後は README 「Hermes Agent › セットアップ」ステップ 3 で ProgramArguments を safehouse ラッパーに差し替え直す

## 検証

```sh
# 壊れた symlink を検出・削除（-y で自動）
sh scripts/remove-broken-symlinks.sh

# 個別リンクの確認例
ls -la ~/.config/fish/config.fish
ls -la ~/.claude/settings.json
```
