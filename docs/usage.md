# 日常操作

[README](../README.md) / 日常操作

| やりたいこと | 手順 |
|---|---|
| 環境変数を追加・変更する | [環境変数の管理](secrets.md#値を追加更新する) |
| 設定を書き換える・配置する | [設定ファイル](#設定ファイルを変更する) |
| アプリを更新・追加・削除する | [Homebrew](#アプリを更新追加削除する) |
| Node・Python などの版を変える | [ランタイム](#ランタイムの版を変える) |
| macOS 設定を適用する | [macOS](#macos-設定を適用する) |
| 外部スキル・plugin を更新する | [外部リポジトリ](#外部スキルと-plugin-を更新する) |
| Hermes を更新・開始・停止する | [Hermes](apps.md#hermes-を停止更新する) |

コマンドは Safehouse 外の通常端末で実行する。全体導入が必要な場合だけ、[setup](setup.md#5-アプリと設定を導入する)を実行する。

以降は家用の `default,private` を例にする。仕事用は `default,work`、共通だけなら `default` に置き換える。構成はすべて明示し、`private` / `work` に `default` は自動追加されない。

## 設定ファイルを変更する

既存設定の本文は `~/dotfiles/config/` 内の正本を編集する。HOME から直接リンクしているため再配置は不要。アプリの再読み込みが必要な場合は、そのアプリの手順に従う。

配置するファイルを追加するときは Git の追跡対象にする。新しい配置先なら [mise.default.toml](../mise.default.toml)などの構成別宣言も更新する。

```fish
mise -C ~/dotfiles -E default,private dot apply --dry-run
```

配置先に不明な実体・別リンクがなければ適用する。

```fish
mise -C ~/dotfiles -E default,private dot apply
```

衝突したら[トラブル対応](troubleshooting.md#設定配置だけ再開する)へ。リンクや管理ディレクトリの削除・改名では、宣言を消す前に対象を解除する。`TARGET` は変更する配置先に置き換える。

```fish
mise -C ~/dotfiles -E default,private dot unapply TARGET
```

## アプリを更新・追加・削除する

アプリ一覧の正本は `brew/Brewfile.{default,private,work}`。選択した一覧だけ導入・更新する家用の例：

```fish
brew bundle --file ~/dotfiles/brew/Brewfile.default
brew bundle --file ~/dotfiles/brew/Brewfile.private
```

Homebrew 本体・tap の情報更新や個別アプリの更新は次で行う。

```fish
brew update
brew upgrade FORMULA
brew upgrade --cask CASK
```

`FORMULA` / `CASK` は対象名に置き換える。全アプリを更新したい場合だけ `brew upgrade` を使う。

追加・削除は対象の Brewfile も変更し、対象だけ `brew install` / `brew uninstall` する。GUI は `--cask` を付ける。宣言から削除しただけではアンインストールされない。

mosh の更新後は署名とファイアウォール登録をやり直す。

```fish
cd ~/dotfiles
bash scripts/allow-mosh-firewall.sh
```

会社が管理するアプリをこの Mac だけ除外したい場合は、[Bundle のスキップ設定](troubleshooting.md#会社が管理するアプリをスキップする)を使う。

## ランタイムの版を変える

[共通ランタイム設定](../config/.config/mise/config.base.toml)の exact 版指定を変更する。

変更後、別プロジェクトの設定が混ざらない HOME を対象に、必要な runtime だけ導入する。Python の例：

```fish
env MISE_ENV= mise -C ~ install python
cd ~
mise which python
python --version
```

AWS CLI は `aqua:aws/aws-cli` を対象にし、更新後は `aws --version` を確認する。

## macOS 設定を適用する

構成別 `mise.<name>.toml` の defaults / defaults_entries と [scripts/macos-settings.sh](../scripts/macos-settings.sh) が正本。

```fish
mise -C ~/dotfiles -E default,private bootstrap macos defaults apply --dry-run
mise -C ~/dotfiles -E default,private bootstrap macos defaults apply
```

キーボードショートカットの変更は、ログアウトして再ログインするまで反映されない。

defaults は対象ユーザーとして書き込む。電源設定の補完は別操作で、sudo 認証後に実行する。

```fish
sudo -v
bash ~/dotfiles/scripts/macos-settings.sh private
```

補完スクリプトの `apply` 確認に応答する。

適用後は `pmset -g custom`、`defaults read com.apple.screensaver idleTime` とシステム設定で確認する。

## 外部スキルと plugin を更新する

取得元とブランチは構成別宣言の `[bootstrap.repos]`、選択するスキルと配置先は `[dotfiles]` に記す。

```fish
mise -C ~/dotfiles -E default,private bootstrap repos update --dry-run
mise -C ~/dotfiles -E default,private bootstrap repos update
mise -C ~/dotfiles -E default,private dot apply --dry-run
mise -C ~/dotfiles -E default,private dot apply
```

この repos 更新に Hermes は含まれない。本体は[専用 task](apps.md#hermes-を停止更新する)で更新する。

更新予定と配置予定を確認する。対象を絞る場合は `bootstrap repos update PATH` で宣言済み checkout を指定する。

fish の bobthefish / fzf、Yazi の git / smart-enter / full-border も setup 時に最新版へ更新される。自作スキルの本文変更・配置は[設定ファイル](#設定ファイルを変更する)と同じ。
