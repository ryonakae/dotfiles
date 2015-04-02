" Vi互換モードをオフ(Vimの拡張機能を有効)
set nocompatible

" ファイル名と内容によってファイルタイプを判別し、ファイルタイププラグインを有効にする
filetype indent plugin on

" neobundleでプラグインを管理
if has('vim_starting')
  set runtimepath+=~/.vim/bundle/neobundle.vim
  call neobundle#begin(expand('~/.vim/bundle/'))
  NeoBundleFetch 'Shougo/neobundle.vim'
  call neobundle#end()
endif

" 以下のプラグインをバンドル
NeoBundle 'Shougo/neobundle.vim'
NeoBundle 'Shougo/vimproc'
NeoBundle 'Shougo/neocomplcache'
NeoBundle 'Shougo/unite.vim'
NeoBundle 'ujihisa/unite-colorscheme'

" カラースキーム
" NeoBundle 'chriskempson/vim-tomorrow-theme'
" colorscheme Tomorrow-Night
NeoBundle 'w0ng/vim-hybrid'
colorscheme hybrid

" シンタックスハイライト
syntax on

" エンコード
set encoding=utf8
" ファイルエンコード
set fileencoding=utf-8

" スクロールする時に下が見えるようにする
set scrolloff=5

" バッファを保存しなくても他のバッファを表示できるようにする
set hidden
" バッファが変更されているとき、コマンドをエラーにするのでなく、保存するかどうか確認を求める
set confirm

" .swapファイルを作らない
set noswapfile
" バックアップファイルを作らない
set nowritebackup
" バックアップをしない
set nobackup

" コマンドライン補完を便利に
set wildmenu

" タイプ途中のコマンドを画面最下行に表示
set showcmd

" OSのクリップボードを使う
set clipboard+=unnamed
set clipboard=unnamed

" 行番号を表示
set number
" 画面最下行にルーラーを表示する
set ruler
" ステータスラインを常に表示する
set laststatus=2

" 対応括弧をハイライト表示する
set showmatch

" 検索語を強調表示(<C-L>を押すと現在の強調表示を解除する)
set hlsearch
" 検索時に大文字・小文字を区別しない。ただし、検索後に大文字小文字が混在しているときは区別する
set ignorecase
set smartcase

" オートインデント
set autoindent
" オートインデント、改行、インサートモード開始直後にバックスペースキーで削除できるようにする
set backspace=indent,eol,start

" 移動コマンドを使ったとき、行頭に移動しない
set nostartofline

" ビープの代わりにビジュアルベル(画面フラッシュ)を使う
set visualbell
" ビジュアルベルも無効化する
set t_vb=

" 全モードでマウスを有効化
set mouse=a

" タブ文字の代わりにスペース2個を使う場合の設定。この場合、'tabstop'はデフォルトの8から変えない
set shiftwidth=2
set softtabstop=2
set expandtab