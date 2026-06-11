# dotfiles

macOS 向け設定ファイル管理リポジトリ。`config/` 配下を `$HOME` にシンボリックリンクして展開する。新規マシンのセットアップ手順と Hermes Agent の運用詳細は `README.md` を参照。

## 編集の基本

- **`config/` 配下のファイルを直接編集する**（`$HOME` の symlink 先は編集しない）
- `config/<path>` が `~/<path>` にそのまま対応する。例:
  - `config/.config/fish/functions/dc.fish` → `~/.config/fish/functions/dc.fish`
  - `config/.claude/settings.json` → `~/.claude/settings.json`
- `*.example` パターン: マシン固有・機密を含むファイルは `.example` をリポジトリ管理し、実ファイルは `.gitignore` で除外（`brew/Brewfile`, `config/.config/fish/config.fish`, `~/.hermes/hindsight/.env` など）
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
├── .pi/agent/                  # Pi Coding Agent 固有
└── .config/agent-safehouse/    # sandbox-exec ポリシー
```

- 共通指示書の正本は `config/.agents/AGENTS.md`（言語・Python 実行・Web 検索ルール等）。`.claude/CLAUDE.md`、`.codex/AGENTS.md`、`.gemini/GEMINI.md`、`.pi/agent/AGENTS.md` はすべてこのファイルへの symlink にする
- スキル配布: `config/.agents/skills/` がグローバル、`config/.claude/skills/` が Claude 専用。`create-skills-symlink.sh` が各エージェントの `skills/` ディレクトリへ symlink する
- 無効化したグローバルスキルは `config/.agents/skills/.disabled/` に移動する。ドットで始まるディレクトリは `create-skills-symlink.sh` の配布対象外
- `config/.agents/skills/` には自作スキルのみを置く。外部スキル（`npx skills add -g ...` で取得するもの）は `~/.agents/skills/` 配下に実体として展開され、`config/.agents/.skill-lock.json`（`~/.agents/.skill-lock.json` の symlink 元）で管理する
- Pi の `pi-hooks` 設定は `config/.pi/agent/hooks.json`、実行スクリプトは `config/.pi/agent/scripts/` に置く。`hooks/` というディレクトリ名は Pi extension として自動読み込みされるため使わない
- エージェント CLI は fish 関数（`safe`, `claude`, `gemini`, `codex`, `hermes` など）経由で agent-safehouse サンドボックス内で起動する
- 共通 sandbox 引数は `config/.config/fish/functions/__safehouse_args.fish`。`--add-dirs` で top-level（`~/.config`, `~/.local`, `~/.cache`, `~/Library/Caches`, `~/dotfiles`, `~/Dev` 等）を列挙する allowlist 型ポリシー。列挙外は safehouse default deny + `--enable=...` の組み合わせで暗黙に閉じる。allow 領域内の機密ファイル名（`.env`, `credentials.json`, 秘密鍵類）と、wide-read で見えるホスト credential（`~/.gnupg`, `~/.aws/credentials` 等）だけを `local-overrides.sb` で後勝ち deny する
- 機密ファイルの deny ルール、vendor 配下の例外 allow、`~/.hermes` の信頼境界 allow は `config/.config/agent-safehouse/local-overrides.sb` に集約。`~/.hermes` は Hermes Agent の workdir かつ信頼境界として、汎用 deny（`.env` 等）を後勝ちで貫通させる
- **`__safehouse_args.fish` と `config/.config/agent-safehouse/safe-hermes-gateway.sh` / `safe-hermes-dashboard.sh` の `--add-dirs` / `--enable` リストは原則同期する**。ただし gateway / dashboard は自律実行向けに `clipboard` / `cleanshot` など対話用 feature を意図的に省く場合がある。片方を変更したら、差分が意図したものか必ず確認する
- Hermes gateway の launchd 操作は `hermes-gateway {start|stop|restart|status|update}` に統一する（`bootout` / `bootstrap` 直叩きはしない）

## Hermes Agent 固有メモ

運用・セットアップ・トラブルシュートは `README.md` の「Hermes Agent」節を参照。

- dotfiles で管理するのは 3 ファイルのみ: `SOUL.md`, `services/docker-compose.yml`, `hindsight/.env.example`
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
