# 日常操作

[README](../README.md) / 日常操作

| やりたいこと | 手順 |
|---|---|
| API キーを追加・変更する | [共通 API キーの追加・更新](secrets.md#値を追加更新する) |
| 設定を書き換える・配置する | [設定ファイル](#設定ファイルを変更する) |
| アプリを更新・追加・削除する | [Homebrew](#アプリを更新追加削除する) |
| Node・Python などの版を変える | [ランタイム](#ランタイムの版を変える) |
| macOS 設定・Nix 基盤を更新する | [Nix](#nix-を更新適用する) |
| 外部スキルを更新する | [外部スキル](#外部スキルを更新する) |
| Hermes を開始・停止する | [Hermes](apps.md#hermes) |

コマンドは通常の端末で実行する。`sh` の例は zsh・fish 共通。構文が異なる箇所は使っている shell の例だけを実行する。

## 設定ファイルを変更する

既存設定の本文は `~/dotfiles/config/` 内の正本を編集する。HOME から直接リンクしているため再配置は不要。アプリの再読み込みが必要な場合は、そのアプリの手順に従う。

配置するファイルを追加するときは、Git の追跡対象にする。新しい配置先なら [mise.toml](../mise.toml) も更新する。

```sh
mise -C ~/dotfiles dot apply --dry-run
```

表示された配置先に不明な実体・別リンクがなければ適用する。

```sh
mise -C ~/dotfiles dot apply
```

衝突は上書きせず[トラブル対応](troubleshooting.md#設定配置だけ再開する)へ。リンクや管理ディレクトリの削除・改名では、宣言を消す前に対象を解除する。`TARGET` は変更する配置先に置き換える。

```sh
mise -C ~/dotfiles dot unapply TARGET
```

## アプリを更新・追加・削除する

通常の CLI / GUI は Homebrew で更新する。

```sh
brew update && brew upgrade
```

対象を絞る場合は `brew upgrade FORMULA` または `brew upgrade --cask CASK` を使う。`FORMULA` / `CASK` は対象名に置き換える。App Store アプリの更新・認証は App Store で行う。

追加・削除は [Nix のアプリ一覧](../nix/darwin/homebrew.nix)も変更し、対象だけ `brew install` / `brew uninstall` する。GUI は `--cask` を付ける。通常アプリの操作に Nix の build / switch は必須ではない。

宣言から削除しただけではアンインストールされない。`--zap` や一括 cleanup は通常の削除に使わない。Unity CLI の `--zap` は Hub のデータも削除対象にする。

自己更新する GUI や `version :latest` の cask は通常の upgrade 対象外になる場合がある。対象の `brew info --cask CASK` と `brew help upgrade` を確認し、必要な対象だけ greedy 更新する。

mosh の更新後は署名とファイアウォール登録をやり直す。

```sh
cd ~/dotfiles
bash scripts/allow-mosh-firewall.sh
```

会社が管理するアプリをこの Mac だけ除外したい場合は、[Bundle のスキップ設定](troubleshooting.md#会社が管理するアプリをスキップする)を使う。

## ランタイムの版を変える

[共通ランタイム設定](../config/.config/mise/config.base.toml)の版指定を変更し、個別プロジェクトの設定が混ざらない HOME から導入する。

```sh
cd ~
mise install
mise which python
python --version
```

変更した runtime について解決先と版を確認する。`mise install` は指定版を入れる操作で、exact pin 自体は更新しない。`mise upgrade` も exact pin を自動では進めない。

AWS CLI も同じ設定で管理する。更新後は `aws --version` を確認する。プロジェクト固有の版は、そのプロジェクトの設定で管理する。

## Nix を更新・適用する

`private` 構成は家用 Mac の常時稼働向け。[電源設定](../nix/hosts/private.nix)で本体・ディスクの自動スリープと電源ボタンによるスリープを無効にし、停電復旧後の自動起動を有効にする。画面は20分でスリープ、スクリーンセーバーはユーザー設定で10分。スクリーンセーバー開始・画面スリープ後のパスワード要求は即時にする。FileVault や自動ログインは変更しないため、再起動後の無人復旧までは保証しない。

適用後は `pmset -g custom` で `sleep 0`・`disksleep 0`・`displaysleep 20`・`autorestart 1`・`Sleep On Power Button 0`、`defaults read com.apple.screensaver idleTime` で `600` を確認する。スクリーンセーバーのマシン固有設定（ByHost）が残っている場合は、ユーザー設定と競合する可能性があるため別途確認する。

### 依存を更新する

構成や設定だけを変えた場合は、この操作は不要。固定版から復元する場合も更新しない。

```sh
cd ~/dotfiles
bash scripts/dotfiles.sh update nixpkgs
git diff -- flake.lock
```

更新する対象に合わせて `nixpkgs` を次の名前に置き換える。

| 名前 | 対象 |
|---|---|
| `nixpkgs` | Bash / fish / mise と Nix 側の依存 |
| `hermes-agent` | Hermes 本体 |
| `nix-homebrew` | Homebrew 本体 |
| `agent-skills` | 外部スキルの管理ライブラリ |
| `all` | 上記を含む全公開 input。外部スキルの取得元は含まない |

更新は lock の変更だけ。差分を確認してから次へ進む。新しい Nix ファイルは対象を指定して Git に追加しておく。

### 設定配置までまとめて適用する

Hermes の起動定義が変わらなければ、稼働したまま適用できる。本体・wrapper・起動環境などの変更で停止を求められた場合だけ、[管理関数で停止](apps.md#hermes-を停止更新する)してから適用する。既存 Home Manager からの切替では、先に[移行手順](migration.md)を済ませる。

macOS 設定を変更する場合は、変更対象だけ現在の値・型・未設定かどうかを控える。Nix の旧世代に戻しても、これらの設定は元に戻らない場合がある。

```sh
cd ~/dotfiles
bash scripts/dotfiles.sh setup --configuration private
```

仕事用は `--configuration work`、共通設定だけなら `--configuration private` を省く。対象と配置予定を確認して承認する。設定リンクの確認後、HOME から `mise install` を実行し、共通設定の指定版を導入する。成功条件は[初回セットアップの確認](setup.md#5-アプリと設定を導入する)と同じ。停止したサービスは、成功確認後に必要なものだけ再開する。

### ビルドと適用を分ける

build は検査・ビルドのみ。switch は指定した成果物の適用のみで、設定配置は行わない。

家用の例。仕事用は `--configuration work` に置き換え、共通構成なら `--configuration private` を省く。

**zsh：**

```zsh
cd ~/dotfiles
system=$(bash scripts/dotfiles.sh build --configuration private)
```

**fish：**

```fish
cd ~/dotfiles
set system (bash scripts/dotfiles.sh build --configuration private)
```

ビルドが成功したら成果物と適用範囲を確認する。[適用前の確認](#設定配置までまとめて適用する)に従って、変更する macOS 設定の旧値を控えてから同じ端末で適用する。Hermes の停止は、起動定義が変わる場合だけ必要。

```sh
bash scripts/dotfiles.sh switch "$system"
```

別端末では変数の代わりに、確認済みの `/nix/store/…-darwin-system-…` パスを渡す。switch に `--configuration` は付けない。古い形式や GC で消えた成果物は、build から準備し直す。

## 外部スキルを更新する

取得元をまとめて更新する。個別の取得元だけを更新する機能はない。

```sh
cd ~/dotfiles
nix run .#skills-sources-lock
git diff -- nix/skill-sources.lock.json
```

差分と選択するスキルを確認し、[Nix のビルド・適用](#ビルドと適用を分ける)へ進む。復元時は更新せず、既存 lock を使う。

取得元の追加は `nix/skill-sources/`、選択は `nix/home/skills.nix` を編集してから同じ更新を行う。`npx skills` による別管理を重ねない。自作スキルの本文変更・配置は[設定ファイル](#設定ファイルを変更する)と同じ。
