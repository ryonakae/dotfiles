dotfiles
=====

Macを新規購入・OSクリーンインストールした時にやるやつ


## XcodeとCommand Line Tools for Xcodeのインストール
gitコマンド使うのと、Homebrewのインストールに必要

* Xcodeインストールする
* `$ xcode-select --install`を実行


## リポジトリをcloneする
ユーザーのホームディレクトリにcloneするのが良さそう

```
$ cd ~/
$ git clone https://github.com/ryonakae/dotfiles.git
```


## シェルスクリプトの実行
`dotfile`ディレクトリに移動し、シェルスクリプトを実行

```
$ cd dotfiles
$ sh setup.sh && source ~/.bash_profile
```

brew-caskで貼られるシンボリックリンクのリンク先が変更される（`~/Applications`から`/Applications`）


## Homebrewのインストール
[Homebrew](http://brew.sh/index_ja.html)のインストール

```
$ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

ちょいちょいインストール用のコマンドが変わるのでサイトに行ってコピペ推奨


## Brew Bundle
### フォーミュラの追加
参考：[Homebrew-bundleとBrewfile - Qiita](http://qiita.com/mather314/items/900ae69eba8d6d980cb2)

```
$ brew tap Homebrew/bundle
```


### brew bundleの実行
Brewfileがあるディレクトリで

```
$ brew bundle
```

Brewfileに記述した処理が実行される


## Vimの設定
```
$ mkdir -p ~/.vim/bundle
$ git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
$ git clone https://github.com/Shougo/vimproc ~/.vim/bundle/vimproc
$ cd ~/.vim/bundle/vimproc
$ make -f make_mac.mak
```

ここまでやるとNeoBundleとVimProcがインストールされたりする

```
$ vim hoge
:NeoBundleInstall
```

とするとVimのプラグインがインストールされる


## デフォルトのShellをzshにする
参考：[[MacOSX]ターミナルのデフォルトShellをzshに変更する方法 - DQNEO起業日記](http://dqn.sakusakutto.jp/2014/05/macosx_shell_chsh_zsh.html)

```
# /etc/shells の末尾に /usr/local/bin/zsh を追記
sudo sh -c 'echo $(which zsh) >> /etc/shells'

# ユーザのデフォルトシェルを変更
chsh -s /usr/local/bin/zsh
```

Shellを再起動でzshがデフォルトになる


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


## RubyとかNode.jsとか設定する
Homebrew経由でインストールしたrbenvとnodebrewを使う

* [rbenv を利用した Ruby 環境の構築 ｜ Developers.IO](http://dev.classmethod.jp/server-side/language/build-ruby-environment-by-rbenv/)
* [nodebrewでNode.jsのインストール - Qiita](http://qiita.com/ombran/items/c59525e429c9c363325d)


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


## brew-caskに無いMacApp
* Adobe系
* [Ember](https://forums.realmacsoftware.com/t/ember-1-8-4-beta-now-updated-with-1-8-5-beta/2911)
* Mangao
* DxO FilmPack 4
* VSCO Film
* HiddenSwitch
* Th-MakerX
* ワコム タブレット ドライバ
  - 一応`wacom-tabet`っていうcaskがあるけど未検証


## 補足
### アプリの設定
当たり前だけど各MacAppの設定は自分でやる

### PHPのインストールで`configure: error: Cannot find OpenSSL's <evp.h>`とかいうエラーが出る場合
参考：[OS X YosemiteにHomebrew + DropboxでPHP環境構築　〜Apache, PHP, MySQL, ComposerをインストールしてFuelPHPの設定まで - Qiita](http://qiita.com/saltyshiomix/items/aacb5f9635c0d3201174)


## 参考
* [pixyzehn/dotfiles](https://github.com/pixyzehn/dotfiles)
* [Macの環境構築にhomebrew-cask+Brewfile便利 - yo_waka's blog](http://waka.github.io/2014/1/19/homebrew_cask.html)
