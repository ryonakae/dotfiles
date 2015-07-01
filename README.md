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


## Brew Bundle
### フォーミュラの追加
参考：[Homebrew-bundleとBrewfile - Qiita](http://qiita.com/mather314/items/900ae69eba8d6d980cb2)

    $ brew tap Homebrew/bundle

なんか元BrewdlerがリネームしてHomebrew-bundleになったらしい  
Brewfileの書き方が変わってるので注意  
`update`とか`doctor`とかができなくなって辛い…


### brew bundleの実行
Brewfileがあるディレクトリで

    $ brew bundle

Brewfileに記述した処理が実行される


## デフォルトのShellをzshにする
参考：[[MacOSX]ターミナルのデフォルトShellをzshに変更する方法 - DQNEO起業日記](http://dqn.sakusakutto.jp/2014/05/macosx_shell_chsh_zsh.html)

    # /etc/shells の末尾に /usr/local/bin/zsh を追記
    sudo sh -c 'echo $(which zsh) >> /etc/shells'

    # ユーザのデフォルトシェルを変更
    chsh -s /usr/local/bin/zsh
    
Shellを再起動でzshがデフォルトになるはず


## Homebrewでインストールしたやつを優先的に利用する
`/etc/paths`の順番を入れ替える

    /usr/local/bin
    /usr/bin
    /bin
    /usr/sbin
    /sbin

`$ exec $SHELL`で反映されるはず


## Vimの設定

    $ mkdir -p ~/.vim/bundle
    $ git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
    $ git clone https://github.com/Shougo/vimproc ~/.vim/bundle/vimproc
    $ cd ~/.vim/bundle/vimproc
    $ make -f make_mac.mak

ここまでやるとNeoBundleとVimProcがインストールされたりする

    $ vim hoge
    :NeoBundleInstall

とするとVimのプラグインがインストールされる


## brew-caskに無いMacApp
* MacAppStoreで配布されているアプリ  
  一覧にしてまとめておきたいけどめんどくさい
* [CleanArchiver](https://www.sopht.jp/cleanarchiver/downloads.html)
* Mangao
* (Airfoil)
* DxO FilmPack 4
* VSCO Film
* ~~GraffitiPot~~
  - 2chの新仕様に対応してない
* HiddenSwitch
* HoudahGPS
* Sculptris
* KORG AudioGate 2.3.1
* ~~Tag~~
  - AppStoreにあるデザイン良い方のTagはID3v2.4でタグが保存されるので使わない方が良い
* Th-MakerX
* CSS Hat 2
* コンテンツ管理アシスタント
* (VMware Fusion)
* ワコム タブレット ドライバ
  - 一応`wacom-tabet`っていうcaskがあるけど未検証
* Logicool ウェブカメラ ドライバ


## 補足
### アプリの設定
当たり前だけど各MacAppの設定は自分でやる

### アプリのアップデート
* brew-caskで入れたアプリは特定のディレクトリにインストールされ、`/Applications`にはシンボリックリンクが貼られる
* 各アプリ内で行われるアップデートなどを行うと、`/Applications/xxxxx.app`というようにシンボリックリンクが.appファイルで上書きされてしまい、brew-caskの管理下から外れてしまう
* 面倒だけど、アップデート通知が来たら、以下のようにする
  1. `/Applications`にあるxxxxx.appファイルを削除
  2. `brew cask uninstall xxxxx && brew cask install xxxxx`

参考：[homebrew-caskでよくあること - Qiita](http://qiita.com/tienlen/items/1a50c7507c8f6454f6c6#2-8)

「cask_upgrade.sh」を実行すると、インストールしたアプリが最新かどうかをチェックして、古いやつだけアップデートしてくれる（ただし古いバージョンはそのまま残る）

* 参考1：[Homebrew-caskのアプリをアップグレードする](http://rcmdnk.github.io/blog/2014/09/01/computer-mac-homebrew/)
* 参考2：[homebrew-cask - brew caskのappどもをupgradeする - Qiita](http://qiita.com/2k0ri/items/9fe8d33a72dbfb15fe6b)

### PHPのインストールで`configure: error: Cannot find OpenSSL's <evp.h>`とかいうエラーが出る場合
参考：[OS X YosemiteにHomebrew + DropboxでPHP環境構築　〜Apache, PHP, MySQL, ComposerをインストールしてFuelPHPの設定まで - Qiita](http://qiita.com/saltyshiomix/items/aacb5f9635c0d3201174)


## 参考
* [pixyzehn/dotfiles](https://github.com/pixyzehn/dotfiles)
* [Macの環境構築にhomebrew-cask+Brewfile便利 - yo_waka's blog](http://waka.github.io/2014/1/19/homebrew_cask.html)
