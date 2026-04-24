# dotfiles

Mac を新規購入・OS クリーンインストールした時にやるやつ

## リポジトリを clone

ユーザーのホームディレクトリに clone する

```
$ cd ~/
$ git clone https://github.com/ryonakae/dotfiles.git
$ cd dotfiles
```

## Xcode Command Line Tools と Homebrew のインストール

```
$ sh scripts/install.sh
```

## \*.example ファイルのコピー

`Brewfile.example` `fish.config.example` などを `Brewfile` `fish.config` にリネームしてコピーする

```
$ sh scripts/copy.sh
```

PC によって設定を変えたいものは適宜コメント or コメントアウト解除

## シンボリックリンクの作成

各設定ファイルのシンボリックリンクをホームディレクトリに貼る

```
$ sh scripts/create-symlink.sh
```

## brew bundle の実行

```
$ cd brew
$ brew bundle -v
```

- Brewfile に記述したものがインストールされる
- 管理者パスワード入れる必要がある場合があるのでターミナルをチラ見しておく

### Homebrew でインストールしたやつを優先的に利用する

fish を使うなら `config.fish` 内の `brew shellenv` と `fish_add_path --move` で Homebrew のパスが先頭側に来る。

それでも GUI アプリや他の shell で `/usr/bin` が先に来る警告が出る場合は、`/etc/paths` の順番を入れ替える。

- Apple Silicon: `/opt/homebrew/bin`
- Intel Mac: `/usr/local/bin`

```
/opt/homebrew/bin
/usr/local/bin
/usr/bin
/bin
/usr/sbin
/sbin
```

設定後に `exec fish` またはターミナル再起動で反映される

## fish の設定

### デフォルトの Shell を fish にする

参考：[ログインシェルを fish にしてみる \- Qiita](https://qiita.com/bleru/items/047a4e8ea2afb654d9e1)

```
# /etc/shells の末尾にfishを追記
$ sudo sh -c 'echo $(which fish) >> /etc/shells'

# ユーザのデフォルトシェルを変更
$ which fish
$ chsh -s <which fishで表示されたパス>
```

Shell を再起動で fish がデフォルトになる

### fishfile に書かれたパッケージをインストール

```
$ fisher update
```

### HOMEBREW_GITHUB_API_TOKEN の設定

- https://github.com/settings/tokens にアクセスして、Homebrew 用のトークンを作成 (既にあれば Regenerate)
- トークンを config.fish の HOMEBREW_GITHUB_API_TOKEN の箇所にコピペ

## Vim の設定

### NeoBundle と VimProc のインストール

```
$ mkdir -p ~/.vim/bundle
$ git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
$ git clone https://github.com/Shougo/vimproc ~/.vim/bundle/vimproc
$ cd ~/.vim/bundle/vimproc
$ make -f make_mac.mak
```

### Vim プラグインのインストール

```
$ vim hoge
:NeoBundleInstall
!q
```

## Ruby、Node、Python とか設定する

[mise](https://mise.jdx.dev/) を使う

### PHP を mise で管理する

- [mise を使って複数の PHP バージョンをインストールする \#PHP \- Qiita](https://qiita.com/yuki777/items/8c71f4535e696a2434b3)
- [asdf\+Homebrew で怠惰に PHP の環境を整える](https://zenn.dev/meihei/articles/85f9c235c666f6)

### ディレクトリごとに環境変数を切り替える

[asdf, direnv をやめて mise に移行する](https://blog.sh1ma.dev/articles/20240108_from_asdf_to_mise)

---

## 日々のメンテナンス

[【Homebrew】コマンド一覧 \#homebrew \- Qiita](https://qiita.com/P-man_Brown/items/82b7e2f1e108a72d89f4)

```
# Homebrew 自体を更新
$ brew update

# 更新可能な formula & cask を表示
$ brew outdated

# 他の formula の依存関係としてのみインストールされ不要となったものをアンインストール
$ brew autoremove

# formula や cask のキャッシュを削除
$ brew cleanup

# システムに問題がないかチェック
$ brew doctor
```

---

## Hermes Agent Gateway（launchd 自動起動）

hermes gateway を agent-safehouse 経由で常駐させるには、launchd plist を safehouse ラッパーに差し替える。

### セットアップ

```sh
# 1. hermes インストール（初回のみ）
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. plist を生成（fish の hermes 関数は safehouse ラッパーなので command で迂回）
command hermes gateway install

# 3. plist の ProgramArguments を safehouse ラッパーに差し替え
#    ProgramArguments を以下に書き換える:
#      <array>
#        <string>/Users/ryo.nakae/.config/agent-safehouse/safe-hermes-gateway.sh</string>
#      </array>
vim ~/Library/LaunchAgents/ai.hermes.gateway.plist

# 4. サービスをロード（RunAtLoad=true で即起動）
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist
```

ラッパースクリプトは `config/.config/agent-safehouse/safe-hermes-gateway.sh`。`hermes gateway install --force` で plist が上書きされるため、再実行時はステップ 3 をやり直す。

### 停止・再起動

```sh
# gateway を停止（plist はアンロードされる）
launchctl bootout gui/$(id -u)/ai.hermes.gateway

# gateway を再起動（停止 → 起動）
launchctl bootout gui/$(id -u)/ai.hermes.gateway
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist

# 稼働確認
curl -sf http://localhost:8642/health
```

---

## その他

### 各 App の設定

- 各 App の設定は自分でやる
- `Dropbox/App` にアプリの設定を保存したりしているので、適宜インポートなど

### Dock の表示/非表示を早くする

```
$ defaults write com.apple.dock autohide-time-modifier -float 0.15;killall Dock
$ defaults write com.apple.dock autohide-delay -float 0;killall Dock
```

### SSH 鍵を新しい PC に丸ごと移行する

[SSH 鍵を新しい PC に移動させる方法（mac） \#SSH \- Qiita](https://qiita.com/yamaking/items/65da45bd69e616f8f88d)

### Homebrew で使われていないものを検索

[Homebrew で使われていない formula を削除する :: by and for engineers](https://yulii.github.io/brew-cleanup-installed-formulae-20200509.html)

```
$ brew list --formula | xargs -I{} sh -c 'brew uses --installed {} | wc -l | xargs printf "%20s is used by %2d formulae.\n" {}' | grep '0 formula'
```

### PHP を Homebrew でインストール・切り替えする

[Mac で複数のバージョンの PHP を同時に使う \#PHP \- Qiita](https://qiita.com/koriym/items/17662cd9c44c43081bf9)

### SourceTree で push できないとき

[SourceTree で GitHub の Personal access tokens を利用する方法](https://zenn.dev/koushikagawa/articles/3c35e503c8553a)
