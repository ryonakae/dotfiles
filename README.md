dotfiles
=====

Macを新規購入・OSクリーンインストールした時にやるやつ


## 1. リポジトリをcloneする
ユーザーのホームディレクトリにcloneするのが良さそう

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
* Airfoil*
* DxO FilmPack 4
* VSCO Film
* GraffitiPot
* HiddenSwitch
* HoudahGPS
* Sculptris Alpha 6
* KORG AudioGate 2.3.1
* Tag
* Th-MakerX
* CSS Hat 2
* コンテンツ管理アシスタント
* VMware Fusion*
* ワコム タブレット ドライバ
* Logicool ウェブカメラ ドライバ


## 補足
### アプリの設定
当たり前だけど各MacAppの設定は自分でやる。

### PHPのインストールで`configure: error: Cannot find OpenSSL's <evp.h>`とかいうエラーが出る場合
参考：[OS X YosemiteにHomebrew + DropboxでPHP環境構築　〜Apache, PHP, MySQL, ComposerをインストールしてFuelPHPの設定まで - Qiita](http://qiita.com/saltyshiomix/items/aacb5f9635c0d3201174)


## 参考

* [pixyzehn/dotfiles](https://github.com/pixyzehn/dotfiles)
* [Macの環境構築にhomebrew-cask+Brewfile便利 - yo_waka's blog](http://waka.github.io/2014/1/19/homebrew_cask.html)