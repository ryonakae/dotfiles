# dotfiles
Macを新規購入・OSクリーンインストールした時にやるやつ


## XcodeとCommand Line Tools for Xcodeのインストール
gitコマンド使うのと、Homebrewのインストールに必要

* Xcodeインストールする
* Xcode起動して規約にAgreeしたり追加コンポーネントをインストールしたりする
* `$ xcode-select --install`を実行


## リポジトリをcloneする
ユーザーのホームディレクトリにcloneするのが良い

```
$ cd ~/
$ git clone https://github.com/ryonakae/dotfiles.git
```


## シェルスクリプトの実行
`dotfile`ディレクトリに移動し、シェルスクリプトを実行

```
$ cd dotfiles
$ sh symlink.sh && source ~/.zshrc
```

各設定ファイルのシンボリックリンクをホームディレクトリに貼る


## Homebrewのインストール
[Homebrew](http://brew.sh/index_ja.html)のインストール

```
$ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

ちょいちょいインストール用のコマンドが変わるのでサイトに行ってコピペ推奨


## brew bundleの実行
1. Brewfile.example を Brewfile にリネーム
  * `$ cp Brewfile.example Brewfile`
2. PCによってインストールしたいものを適宜コメントアウト解除
3. `$ brew bundle`を実行

Brewfileに記述した処理が実行される


## デフォルトのShellをfishにする
参考：[ログインシェルをfishにしてみる \- Qiita](https://qiita.com/bleru/items/047a4e8ea2afb654d9e1)

```
# /etc/shells の末尾に /usr/local/bin/fish を追記
$ sudo sh -c 'echo $(which fish) >> /etc/shells'

# ユーザのデフォルトシェルを変更
$ chsh -s /usr/local/bin/fish
```

Shellを再起動でfishがデフォルトになる


## fishの設定
### fishfileに書かれたパッケージをインストール
```
$ fisher update
```


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
```

とするとVimのプラグインがインストールされる


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
Homebrew経由でインストールしたanyenvを使う

* [オールインワンな開発環境をanyenvで構築する](https://zenn.dev/ryuu/articles/use-anyversions)


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

ちなみにフォントは、基本的にはRightFont + Dropboxで管理したい


## 日々のメンテナンス
```
$ sh maintenance.sh
```

もろもろのHomebrewのアップデートとかクリーンナップをまとめてやる


## その他
* 当たり前だけど各Appの設定は自分でやる

### Dockの表示/非表示を早くする
```
$ defaults write com.apple.dock autohide-time-modifier -float 0.15;killall Dock
$ defaults write com.apple.dock autohide-delay -float 0;killall Dock
```


## 参考
* [pixyzehn/dotfiles](https://github.com/pixyzehn/dotfiles)
