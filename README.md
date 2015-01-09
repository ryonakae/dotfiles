dotfiles
=====


## 1. リポジトリをcloneする

    $ cd ~/
    $ git clone https://github.com/ryonakae/dotfiles.git


## 2. シェルスクリプトの実行
`dotfile`ディレクトリに移動し、シェルスクリプトを実行

    $ cd dotfiles
    $ sh setup.sh && source ~/.bash_profile

brew-caskで貼られるシンボリックリンクのリンク先が変更される（`~/Applications`から`/Applications`）


## XcodeとCommand Line Tools for Xcodeのインストール
Homebrewのインストールに必要


## Homebrewのインストール
[Homebrew](http://brew.sh/index_ja.html)のインストール

    $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

ちょいちょいインストール用のコマンドが変わるのでサイトに行ってコピペ推奨


## brew-cask
### homebrew/boneyardリポジトリの追加
`brew bundle`はもうオワコンらしいけど、homebrew/boneyardを追加すると使えるようになる。動作しなくなるまでは使いたい

    $ brew tap homebrew/boneyard


### brew bundleの実行

    $ brew bundle

Brewfileに記述した処理が実行される


### brew-caskに無いMacApp

* MacAppStoreで配布されているアプリ
  一覧にしてまとめておきたいけどめんどくさい
* [CleanArchiver](https://www.sopht.jp/cleanarchiver/downloads.html)
* Mangao


### 補足
当たり前だけど各MacAppの設定は自分でやる。


## 参考

* [pixyzehn/dotfiles](https://github.com/pixyzehn/dotfiles)
* [Macの環境構築にhomebrew-cask+Brewfile便利 - yo_waka's blog](http://waka.github.io/2014/1/19/homebrew_cask.html)