# 日常操作

[README](../README.md) / 日常操作

| やりたいこと | 手順 |
|---|---|
| API キーを追加・変更する | [共通 API キー](secrets.md#値を追加更新する) |
| 設定を書き換える・配置する | [設定ファイル](#設定ファイルを変更する) |
| アプリを更新・追加・削除する | [Homebrew](#アプリを更新追加削除する) |
| Node・Python などの版を変える | [ランタイム](#ランタイムの版を変える) |
| macOS 設定を適用する | [macOS](#macos-設定を適用する) |
| 外部スキル・plugin を更新する | [外部リポジトリ](#外部スキルと-plugin-を更新する) |
| Hermes を更新・開始・停止する | [Hermes](apps.md#hermes-を停止更新する) |

コマンドは Safehouse 外の通常端末で実行する。部分操作は Homebrew / mise の標準コマンドを使う。全体導入が必要な場合だけ、[setup](setup.md#5-アプリと設定を導入する)を実行する。全体 setup は選択したアプリと外部リポジトリの更新も伴い、無変更の操作ではない。

以降は家用の `default,private` を例にする。仕事用は `default,work`、共通だけなら `default` に置き換える。構成はすべて明示し、`private` / `work` に `default` は自動追加されない。mise の `-E` を省くと、空のルート `mise.toml` だけでは共通リンクを配置できない。

## 設定ファイルを変更する

既存設定の本文は `~/dotfiles/config/` 内の正本を編集する。HOME から直接リンクしているため再配置は不要。アプリの再読み込みが必要な場合は、そのアプリの手順に従う。

配置するファイルを追加するときは Git の追跡対象にする。新しい配置先なら [mise.default.toml](../mise.default.toml)などの構成別宣言も更新する。ルート `mise.toml` に共通リソースを戻さない。

```fish
mise -C ~/dotfiles -E default,private dot apply --dry-run
```

配置先に不明な実体・別リンクがなければ適用する。

```fish
mise -C ~/dotfiles -E default,private dot apply
```

衝突は上書きせず[トラブル対応](troubleshooting.md#設定配置だけ再開する)へ。リンクや管理ディレクトリの削除・改名では、宣言を消す前に対象を解除する。`TARGET` は変更する配置先に置き換える。

```fish
mise -C ~/dotfiles -E default,private dot unapply TARGET
```

## アプリを更新・追加・削除する

アプリ一覧の正本は `brew/Brewfile.{default,private,work}`。選択した一覧だけ導入・更新する家用の例：

```fish
brew bundle --file ~/dotfiles/brew/Brewfile.default
brew bundle --file ~/dotfiles/brew/Brewfile.private
```

各コマンドの成功後に次へ進む。標準 Bundle の更新を使い、`--no-upgrade` や自動 cleanup は付けない。Homebrew 本体・tap の情報更新や個別アプリの更新は次で行う。

```fish
brew update
brew upgrade FORMULA
brew upgrade --cask CASK
```

`FORMULA` / `CASK` は対象名に置き換える。App Store アプリの更新・認証は App Store でも確認する。全アプリを更新したい場合だけ `brew upgrade` を使う。

追加・削除は対象の Brewfile も変更し、対象だけ `brew install` / `brew uninstall` する。GUI は `--cask` を付ける。宣言から削除しただけではアンインストールされない。`--zap` や一括 cleanup は通常の削除に使わない。Unity CLI の `--zap` は Hub のデータも削除対象にする。

自己更新する GUI や `version :latest` の cask は通常の upgrade 対象外になる場合がある。`brew info --cask CASK` と `brew help upgrade` を確認し、必要な対象だけ greedy 更新する。

mosh の更新後は署名とファイアウォール登録をやり直す。

```fish
cd ~/dotfiles
bash scripts/allow-mosh-firewall.sh
```

会社が管理するアプリをこの Mac だけ除外したい場合は、[Bundle のスキップ設定](troubleshooting.md#会社が管理するアプリをスキップする)を使う。

## ランタイムの版を変える

[共通ランタイム設定](../config/.config/mise/config.base.toml)の exact 版指定を変更する。共通 Node / Python / Ruby / Bun と AWS CLI の指定版は、通常 setup では変更しない。個別プロジェクトの設定も変更しない。

変更後、別プロジェクトの設定が混ざらない HOME を対象に、必要な runtime だけ導入する。Python の例：

```fish
env MISE_ENV= mise -C ~ install python
cd ~
mise which python
python --version
```

`mise install` は指定版を入れる操作で、exact pin 自体は更新しない。包括的な `mise upgrade` は runtime や Hermes の個別更新の代わりに使わない。AWS CLI は `aqua:aws/aws-cli` を対象にし、更新後は `aws --version` を確認する。

## macOS 設定を適用する

構成別 `mise.<name>.toml` の defaults / defaults_entries と [scripts/macos-settings.sh](../scripts/macos-settings.sh) が正本。適用前に変更対象の旧値・型・未設定状態を控える。宣言を戻すだけでは preferences は復旧しない。

```fish
mise -C ~/dotfiles -E default,private bootstrap macos defaults apply --dry-run
mise -C ~/dotfiles -E default,private bootstrap macos defaults apply
```

キーボードショートカットの変更は、ログアウトして再ログインするまで反映されない。

defaults は対象ユーザーとして書き込む。mise 全体を sudo で起動しない。電源設定の補完は別操作で、対象を確認して sudo 認証後に実行する。

```fish
sudo -v
bash ~/dotfiles/scripts/macos-settings.sh private
```

補完スクリプトの `apply` 確認に応答する。`default` の補完は何も行わず、`private` は `systemsetup`、`work` は電源別 `pmset` を使う。選択していない構成の補完を実行しない。

家用では本体・ディスクの自動スリープと電源ボタンによるスリープを無効にし、停電復旧後の自動起動を有効にする。画面は20分、共通のスクリーンセーバーは10分、パスワード要求は即時。FileVault と自動ログインは変更しないため、再起動後の無人復旧は保証しない。

適用後は `pmset -g custom`、`defaults read com.apple.screensaver idleTime` とシステム設定で確認する。ByHost のスクリーンセーバー設定が残る場合は個別に確認する。Dock や端末の自動再起動はしない。必要な再起動・ログアウトは作業を保存して手動で行う。

## 外部スキルと plugin を更新する

取得元とブランチは構成別宣言の `[bootstrap.repos]`、選択するスキルと配置先は `[dotfiles]` に記す。取得元のブランチ最新版への追従を許容し、新しいスキルは自動追加しない。

```fish
mise -C ~/dotfiles -E default,private bootstrap repos update --dry-run
mise -C ~/dotfiles -E default,private bootstrap repos update
mise -C ~/dotfiles -E default,private dot apply --dry-run
mise -C ~/dotfiles -E default,private dot apply
```

この repos 更新に Hermes は含まれない。本体は[専用 task](apps.md#hermes-を停止更新する)で更新する。

更新予定と配置予定を確認し、各操作が成功してから次へ進む。対象を絞る場合は `bootstrap repos update PATH` で宣言済み checkout を指定する。dirty checkout や origin 不一致で止まったら、変更を捨てず確認する。宣言の削除だけでは checkout は削除されない。

fish の bobthefish / fzf、Yazi の git / smart-enter / full-border も setup 時の最新版更新を許容する。宣言済みの取得・配置方式と別の plugin manager を重ねず、更新後は読み込みを確認する。自作スキルの本文変更・配置は[設定ファイル](#設定ファイルを変更する)と同じ。`npx skills` による別管理を重ねない。
