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
- 共通ツール用の秘密は `config/.config/.env`（Git管理外）をdotenvxで暗号化し、`~/.config/.env`から起動時に注入する。テンプレートは `.env.example`、復号鍵はmacOS Keychain。実秘密・実鍵の初期移行はユーザーが行う。手順はREADME「共通ツール用の秘密」を参照
- EditorConfig: スペース 2、LF、UTF-8

## scripts/

- `scripts/copy.sh` — `*.example` を実ファイルへコピー（既存はスキップ）
- `scripts/create-symlink.sh` — `config/` を `$HOME` に symlink（`.DS_Store`, `*.example`, `skills/` はスキップ）
- `scripts/create-skills-symlink.sh` — 共通スキルと Claude 専用スキルを配布し、Antigravity CLI から共通スキルへの参照リンクを作成
- `scripts/remove-broken-symlinks.sh` — 壊れた symlink を対話的に削除（`-y` で自動）
- `scripts/install.sh` — Xcode CLI Tools と Homebrew（新規マシン向け、初回のみ）
- `scripts/allow-mosh-firewall.sh` — `mosh-server` を ad-hoc 署名して macOS ファイアウォールの着信許可に登録（`brew upgrade mosh` で実体パスが変わるたびに再実行）

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
- スキル配布: `config/.agents/skills/` がグローバル、`config/.claude/skills/` が Claude 専用。`create-skills-symlink.sh` が `~/.agents/skills/` と `~/.claude/skills/` へ symlink する。Antigravity CLI は `~/.gemini/antigravity-cli/skills` → `~/.agents/skills` のディレクトリ symlink で共通スキル全体を参照する（同スクリプトで作成）。Claude 専用スキルは含めない。それ以外（`~/.hermes/skills`、`~/.pi/skills`、その他の `~/.gemini/**`）には配布しない
- 無効化したグローバルスキルは `config/.agents/skills/.disabled/` に移動する。ドットで始まるディレクトリは `create-skills-symlink.sh` の配布対象外
- `config/.agents/skills/` には自作スキルのみを置く。外部スキル（`npx skills` で取得するもの）は `~/.agents/skills/` 配下に実体として展開され、`config/skills-lock.json`（`~/skills-lock.json` の symlink 元）で管理する。詳細な運用は `README.md` の「外部スキル（npx skills）」節を参照
- Pi の extension 一覧は `config/.pi/agent/settings.json`、extension 個別設定は原則 `config/.pi/agent/extensions/<extension-name>/`、subagent 定義は `config/.pi/agent/agents/*.md` に置く。保存先を固定する外部 extension は実装に従う。`hooks/` というディレクトリ名は Pi extension として自動読み込みされるため使わない
- Pi のサブエージェント設定は `config/.pi/agent/subagents.json`、親によるモデル・thinking 選定方針と比較データは同ディレクトリの `agent-tool-description.md` で管理する。構成・更新方法は README の「Pi の拡張・MCP」を参照
- エージェント CLI は fish 関数（`safe`, `claude`, `gemini`, `codex`, `hermes` など）経由で agent-safehouse サンドボックス内で起動する
- 環境変数は `--env` で全継承する。共通dotenvx注入とrmの優先PATHは `config/.config/agent-safehouse/run-with-agent-env.sh`。復号失敗、rmラッパーや保護profileの欠落では起動を止める
- 共通sandbox引数は `config/.config/fish/functions/__safehouse_args.fish`。HOMEを原則読み書き可能にし、`compatibility.sb`でファイル以外のIPCを緩和した後、`local-overrides.sb`で秘密・私的データを拒否する。管理wrapper・設定ファイルの編集と親ディレクトリの移動は独自に禁止しない。3つの起動経路で`--allow-profile-writes`を指定する。実行中のsandboxには変更が反映されないため、現在の制限に従って編集し、次回起動から適用する。検証は変更した設定の構文・差分と必要な小さな動作確認に絞る
- 通常のrmは `config/.local/bin/rm` でgomiへ転送する。実rmへfallbackしない。ごみ箱内容への通常の直接アクセスはSandbox内で拒否し（既存のHermes信頼領域は例外）、復元/手動掃除は人間がSandbox外で行う。特殊な移動迂回の完全封鎖は保証しない。絶対パスrm、言語API、Git等による削除・上書きは転送対象外
- Git向けに`.secrets`の一覧・メタデータと直下の`.gitkeep`、Android開発向けに`~/.android/debug.keystore`を許可する。他の秘密ファイルの内容や署名鍵は保護する。完全隔離ではなく互換性優先の直接アクセス制限とし、詳細はREADME「Safehouseの許可と保護」を参照
- 機密ファイルの deny ルール、vendor 配下の例外 allow、`~/.hermes` の信頼境界 allow は `config/.config/agent-safehouse/local-overrides.sb` に集約。`~/.hermes` は Hermes Agent の workdir かつ信頼境界として、汎用 deny（`.env` 等）を後勝ちで貫通させる
- **`__safehouse_args.fish` と `config/.config/agent-safehouse/safe-hermes-gateway.sh` / `safe-hermes-dashboard.sh` のHOME許可・全環境継承・profile順と `--enable` リストは原則同期する**。ただし gateway / dashboard は自律実行向けに `clipboard` / `cleanshot` など対話用 feature を意図的に省く場合がある。片方を変更したら、差分が意図したものか必ず確認する
- Hermes gateway の launchd 操作は `hermes-gateway {start|stop|restart|status|update}` に統一する（`bootout` / `bootstrap` 直叩きはしない）

## Hermes Agent 固有メモ

運用・セットアップ・トラブルシュートは `README.md` の「Hermes Agent」節を参照。

- `config/.hermes/` で管理するのは `SOUL.md`, `mise.toml`, `services/docker-compose.yml`, `hindsight/.env.example`。`mise.toml` は Hermes 配下の Python / Node.js バージョンを固定し、ランタイム本体と `venv` は管理しない
- 管理対象外: `config.yaml`（クレデンシャル）、`hooks/` / `cron/` / `automations/` / `skills/hermes-custom/`（自己改善で書き換わる）、memory / session / 認証系全般
- `hermes gateway install --force` / `start` / `setup` の一部分岐は plist を再生成するため、実行後は README 「Hermes Agent › セットアップ」ステップ 3 で ProgramArguments を safehouse ラッパーに差し替え直す

## Herdr 固有メモ

運用は `README.md` の「Herdr」節を参照。

- dotfiles で管理するのは `config/.config/herdr/config.toml`、補助スクリプト `config/.config/herdr/scripts/*`、プラグイン設定 `config/.config/herdr/plugins/config/<plugin_id>/config.toml`
- 管理対象外: `plugins.json`（絶対パスと commit hash を含む）、`plugins/` の実体、session / log / socket
- プラグインは lock で復元できない。追加・削除したら README の一覧表を更新する

## 検証

```sh
# 壊れた symlink を検出・削除（-y で自動）
sh scripts/remove-broken-symlinks.sh

# 個別リンクの確認例
ls -la ~/.config/fish/config.fish
ls -la ~/.claude/settings.json
```
