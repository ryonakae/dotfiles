# dotfiles
Macを新規購入・OSクリーンインストールした時にやるやつ


## XcodeとCommand Line Tools for Xcodeのインストール
gitコマンド使うのと、Homebrewのインストールに必要

* Xcodeインストールする
* Xcode起動して規約にAgreeしたり追加コンポーネントをインストールしたりする
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
$ sh symlink.sh && source ~/.bashrc
```


## Homebrewのインストール
[Homebrew](http://brew.sh/index_ja.html)のインストール

```
$ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

ちょいちょいインストール用のコマンドが変わるのでサイトに行ってコピペ推奨


## brew bundleの実行
1. Brewfile.example を Brewfile にリネーム
2. PCによってインストールしたいものを適宜コメントアウト解除
3. `$ brew bundle`を実行

Brewfileに記述した処理が実行される


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
### Fisherをインストール
[jorgebucaran/fisher](https://github.com/jorgebucaran/fisher)

```
$ curl https://git.io/fisher --create-dirs -sLo ~/.config/fish/functions/fisher.fish
```

### fishfileに書かれたパッケージをインストール
```
$ fisher
```

### powerlineフォント
[powerline/fonts](https://github.com/powerline/fonts)

### nerdフォント
* [ryanoasis/nerd\-fonts](https://github.com/ryanoasis/nerd-fonts)
* [nerd\-fonts/patched\-fonts/SourceCodePro](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/SourceCodePro)


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
Homebrew経由でインストールしたrbenvとnodenvを使う

* [rbenv を利用した Ruby 環境の構築 ｜ Developers.IO](http://dev.classmethod.jp/server-side/language/build-ruby-environment-by-rbenv/)
* [Nodenv環境を用意する \- Qiita](https://qiita.com/YuukiMiyoshi/items/080b6cde332d8d4e06f3)


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
* Adobe
  - CreativeCloudから手動インストール
* VSCO Film
* ペンタブのドライバ
  - 一応`wacom-tabet`っていうcaskがあるけど未検証
* Cinema 4D


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
