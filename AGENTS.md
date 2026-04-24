# dotfiles

macOS 向け設定ファイル管理リポジトリ。`config/` 配下のファイルを `$HOME` にシンボリックリンクして展開する。

## セットアップ

新規マシンへの適用は以下の順で実行する。

```sh
# 1. Xcode CLI Tools と Homebrew のインストール
sh scripts/install.sh

# 2. *.example ファイルを実ファイルとしてコピー（機密情報を記入する）
sh scripts/copy.sh

# 3. config/ 配下を $HOME にシンボリックリンク
sh scripts/create-symlink.sh

# 4. AI エージェントのスキルをシンボリックリンク
sh scripts/create-skills-symlink.sh

# 5. Homebrew パッケージの一括インストール
cd brew && brew bundle -v
```

## ディレクトリ構造

```
dotfiles/
├── brew/                   # Homebrew パッケージ管理
│   ├── Brewfile            # 実ファイル（.gitignore で除外）
│   └── Brewfile.example    # テンプレート
├── config/                 # $HOME のミラー構造（後述）
├── scripts/                # セットアップ・管理スクリプト
└── AGENTS.md               # このファイル
```

### config/ の配置規則

`config/` 配下のパス構造が `$HOME` の構造をそのまま反映する。

- `config/.config/fish/functions/dc.fish` → `~/.config/fish/functions/dc.fish`
- `config/.claude/settings.json` → `~/.claude/settings.json`

**シンボリックリンクのスキップ対象**: `.DS_Store`、`*.example`、`skills/`（スキルは `create-skills-symlink.sh` で個別管理）

### .example パターン

マシン固有の情報や機密情報を含むファイルは `.example` 付きでリポジトリ管理し、実ファイルは `.gitignore` で除外する。

- `brew/Brewfile.example` → `brew/Brewfile`（実体、gitignore 済み）
- `config/.config/fish/config.fish.example` → `config/.config/fish/config.fish`（実体、gitignore 済み）

`copy.sh` は `*.example` → 同名ファイルのコピーを自動化する（既存ファイルはスキップ）。

## 設定ファイルの編集

- **`config/` 配下のファイルを直接編集する**（作業場所を `dotfiles/` に統一する）
- EditorConfig: インデントはスペース2、改行は LF、文字コードは UTF-8
- 機密情報（APIキー、トークンなど）を `*.example` ファイルに含めない

## AI エージェント設定

```
config/
├── .agents/                    # 全エージェント共通（AGENTS.md、グローバルスキル、通知フック）
├── .claude/                    # Claude Code 固有設定（settings.json、スキル、フック）
├── .codex/                     # Codex 固有設定
├── .gemini/                    # Gemini CLI 固有設定
└── .config/agent-safehouse/    # agent-safehouse のサンドボックスポリシー
```

- `config/.agents/AGENTS.md` は全エージェントの共通指示書（言語・Python実行・Web検索のルールなど）
- グローバルスキルは `config/.agents/skills/`、Claude 固有スキルは `config/.claude/skills/`
- スキルのシンボリックリンクは `scripts/create-skills-symlink.sh` で管理
- エージェントは fish 関数（`safe`, `claude`, `gemini`, `codex`, `hermes` 等）経由で agent-safehouse のサンドボックス内で実行される。共通引数は `__safehouse_args.fish`、機密ファイルの deny ルールは `local-overrides.sb` で管理
- Hermes Agent 専用の deny ルールは `hermes-overrides.sb` で管理（パーソナルディレクトリ遮断、Library 遮断、他エージェント設定の write deny）
- `hermes.fish` と `safe-hermes-gateway.sh` は同じ safehouse 引数を持つ（fish/bash の重複）。片方を変更したら必ず他方も同期する

### Hermes Agent Gateway

`hermes gateway install --force` で plist が上書きされるため、再実行時は plist の ProgramArguments を safehouse ラッパーに差し替え直す必要がある。手順は README.md を参照。

## 検証

シンボリックリンクが正しく張られているか確認する。

```sh
# 壊れたシンボリックリンクを対話的に削除（-y で自動削除）
sh scripts/remove-broken-symlinks.sh

# 特定リンクを手動確認
ls -la ~/.config/fish/config.fish
ls -la ~/.claude/settings.json
```
