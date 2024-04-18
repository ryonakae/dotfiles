# dotfiles
Macを新規購入・OSクリーンインストールした時にやるやつ


## リポジトリをcloneする
ユーザーのホームディレクトリにcloneする

```
$ cd ~/
$ git clone https://github.com/ryonakae/dotfiles.git
```


## XcodeとCommand Line Tools for Xcodeのインストール
gitコマンド使うのと、Homebrewのインストールに必要

* App StoreからXcodeをインストールする
* `$ xcode-select --install`を実行


## config.fishファイルのコピー
* config.fish.example を config.fish にリネーム
  * `$ cp config.fish.example config.fish`
* PCによって設定したいものは適宜コメント or コメントアウト解除


## シェルスクリプトの実行
`dotfile`ディレクトリに移動し、シェルスクリプトを実行

```
$ cd dotfiles
$ sh symlink.sh
```

各設定ファイルのシンボリックリンクをホームディレクトリに貼る


## デフォルトのShellをfishにする
参考：[ログインシェルをfishにしてみる \- Qiita](https://qiita.com/bleru/items/047a4e8ea2afb654d9e1)

```
# /etc/shells の末尾にfishを追記
$ sudo sh -c 'echo $(which fish) >> /etc/shells'

# ユーザのデフォルトシェルを変更
$ which fish
$ chsh -s <which fishで表示されたパス>
```

Shellを再起動でfishがデフォルトになる

### fishがおかしい場合
* `~/.config/fish/config.fish` がちゃんとエイリアスになっているか確認する
* なっていない場合 (ファイルが実在する場合) は、一度ファイルを消して、`$ cd ~/dotfiles && sh symlink.sh` を実行


## fishの設定
### fishfileに書かれたパッケージをインストール
```
$ fisher update
```

### HOMEBREW_GITHUB_API_TOKENの設定
* https://github.com/settings/tokens にアクセスして、Homebrew用のトークンを作成 (既にあればRegenerate)
* トークンをconfig.fishのHOMEBREW_GITHUB_API_TOKENの箇所にコピペ


## Vimの設定
```
$ mkdir -p ~/.vim/bundle
$ git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
$ git clone https://github.com/Shougo/vimproc ~/.vim/bundle/vimproc
$ cd ~/.vim/bundle/vimproc
$ make -f make_mac.mak
```

ここまでやるとNeoBundleとVimProcがインストールされる

```
$ vim hoge
:NeoBundleInstall
!q
```

とするとVimのプラグインがインストールされる


## Homebrewのインストール
[Homebrew](https://brew.sh/ja/)のインストール

```
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

※ちょいちょいインストール用のコマンドが変わるのでサイトに行ってコピペ推奨


## brew bundleの実行
1. Brewfile.example を Brewfile にリネーム
  * `$ cp Brewfile.example Brewfile`
2. PCによってインストールしたいものを適宜コメントアウト解除
3. `$ brew bundle`を実行

Brewfileに記述した処理が実行される


## Homebrewでインストールしたやつを優先的に利用する
`/etc/paths`の順番を入れ替える

```
/usr/local/bin
/usr/bin
/bin
/usr/sbin
/sbin
```

`$ exec $SHELL`で反映される


## Ruby, Node, Pythonとか設定する
Homebrew経由でインストールしたanyenvを使う

[オールインワンな開発環境をanyenvで構築する](https://zenn.dev/ryuu/articles/use-anyversions)

PHPはphpenvではなくHomebrewを使うのが良い


## direnvの設定する
ディレクトリごとに環境変数の設定ができて便利  
例えば、特定ディレクトリ以下でGitHubアカウントを会社のものに切り替えたりできる

* [direnvを使おう - Qiita](http://qiita.com/kompiro/items/5fc46089247a56243a62)
* [direnvを使って複数のgitコミッタ名を切り替える - MANA-DOT](http://blog.manaten.net/entry/direnv_git_account)

### 使い方
```
# 環境変数切り替えたいディレクトリに移動
$ cd ~/Projects/Private

# .envrcの作成、編集(Vimが起動する)
$ direnv edit .
```

`.envrc`に以下のように書く

```
export GIT_COMMITTER_NAME="YOUR NAME"
export GIT_COMMITTER_EMAIL="mail@example.com"
export GIT_AUTHOR_NAME="YOUR NAME"
export GIT_AUTHOR_EMAIL="mail@example.com"
```


## プログラミング用フォント
* 英語フォント
  * [SauceCodePro Nerd Font](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/SourceCodePro)
  * 「Sauce Code Pro Nerd Font Complete」を使う
* 日本語フォント
  * [Source Han Code JP](https://github.com/adobe-fonts/source-han-code-jp)

ちなみにフォントはRightFont + Dropboxで管理したい

* Rightfontを起動し、Open Library -> Dropboxに保存してるライブラリを選択
* Sauce Code Pro Nerd Font, Source Han Code JPを有効化


## 各Appの設定
* 当たり前だけど各Appの設定は自分でやる
* Dropbox/App にアプリの設定を保存したりしている


## その他

### Dockの表示/非表示を早くする
```
$ defaults write com.apple.dock autohide-time-modifier -float 0.15;killall Dock
$ defaults write com.apple.dock autohide-delay -float 0;killall Dock
```

### SSH鍵を新しいPCに丸ごと移行する
[SSH鍵を新しいPCに移動させる方法（mac） \#SSH \- Qiita](https://qiita.com/yamaking/items/65da45bd69e616f8f88d)

### Homebrewで使われていないものを検索
[Homebrew で使われていない formula を削除する :: by and for engineers](https://yulii.github.io/brew-cleanup-installed-formulae-20200509.html)

```
$ brew list --formula | xargs -I{} sh -c 'brew uses --installed {} | wc -l | xargs printf "%20s is used by %2d formulae.\n" {}' | grep '0 formula'
```

### PHPをHomebrewでインストール・切り替えする
[Macで複数のバージョンのPHPを同時に使う \#PHP \- Qiita](https://qiita.com/koriym/items/17662cd9c44c43081bf9)


## 日々のメンテナンス
[【Homebrew】コマンド一覧 \#homebrew \- Qiita](https://qiita.com/P-man_Brown/items/82b7e2f1e108a72d89f4)

```
# Homebrew自体を更新
$ brew update

# 更新可能なformula & caskを表示
$ brew outdated

# 他のformulaの依存関係としてのみインストールされ不要となったものをアンインストール
$ brew autoremove

# formulaやcaskのキャッシュを削除
$ brew cleanup

# システムに問題がないかチェック
$ brew doctor
```


## 参考
* [pixyzehn/dotfiles](https://github.com/pixyzehn/dotfiles)
