# dotfiles

macOS の開発環境と AI エージェントの設定を、新しい Mac に引き継ぐための個人用 dotfiles。
`config/` のファイルをホームディレクトリへシンボリックリンクして使う。

Nix への移行は準備中。[初回導入](docs/setup.md#nix-の初回導入)と[事前ビルド](docs/setup.md#nix-の事前ビルド)は利用できるが、以下の既存環境はまだ切り替えない。適用入口の制約は [適用と復旧準備](docs/setup.md#nix-の適用と復旧準備)を参照。

## Install

既存の設定をバックアップし、sandbox 外のターミナルで実行する。
Git が未導入なら、先に `xcode-select --install` で Command Line Tools を導入する。

```fish
git clone https://github.com/ryonakae/dotfiles.git ~/dotfiles
cd ~/dotfiles
bash scripts/install.sh
bash scripts/copy.sh
```

Homebrew の初回導入後は、インストーラーが案内する PATH 設定を済ませる。
`brew/Brewfile` と `config/.config/fish/config.fish` をマシンに合わせて編集してから次へ進む。

## Quickstart

```fish
cd ~/dotfiles
brew bundle --file=brew/Brewfile -v
uv run --no-project python -c 'pass'
bash scripts/create-symlink.sh
bash scripts/create-skills-symlink.sh
ls -l ~/.config/fish/config.fish
```

最後の出力が dotfiles 内の設定を指していれば配布完了。
配布スクリプトは既存ファイルを上書きしないため、スキップ一覧を確認し、置き換えるものだけ手動で退避して再実行する。
特に `~/.local/bin/rm` は gomi への転送に使うので、古い実体を残さない。

fish を開き、プラグインとランタイムを導入する。

```fish
fisher update
mise install
```

ログインシェルも変更する場合は、`command -s fish` のパスを `/etc/shells` に登録してから `chsh -s (command -s fish)` を実行する。
AI エージェントの起動前に、[共通ツール用の秘密](docs/setup.md#共通ツール用の秘密)を設定する。

## 外部スキル

自作スキルはこのリポジトリ、外部スキルは `~/skills-lock.json` で管理する。
外部スキルは配布先を絞る必要があるため、追加・更新・復元には[外部スキルの手順](docs/setup.md#外部スキル)を使う。
iOS Simulator の検証は [use-agent-device](config/.agents/skills/use-agent-device/SKILL.md) を参照する。

## 運用

- **エージェント:** fish の起動関数から Safehouse 内で使う。HOME への広いアクセスを許可する互換性重視の構成で、完全隔離は保証しない。
- **削除と復元:** 通常の `rm` は gomi に転送する。Finder とは別のごみ箱を使い、絶対パスの `rm`、Git、言語 API による削除・上書きは対象外。[復元手順](docs/setup.md#削除したファイルの復元)を参照。
- **常駐サービス:** [Hermes のセットアップ](docs/setup.md#hermes-agent)と [Herdr の復元](docs/setup.md#herdr)は、dotfiles の配布とは別に行う。
- **mosh:** Homebrew で更新するたびに `bash scripts/allow-mosh-firewall.sh` を実行し、署名とファイアウォール登録をやり直す。

Pi の導入拡張は [settings.json](config/.pi/agent/settings.json) を参照する。
設定や拡張を更新した後は Pi を起動し直す。
このリポジトリを編集するときの制約は [AGENTS.md](AGENTS.md) に記載する。
