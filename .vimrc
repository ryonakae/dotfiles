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
call neobundle#begin(expand('~/.vim/bundle/'))
  NeoBundle 'Shougo/neobundle.vim'
  NeoBundle 'Shougo/vimproc', {
    \ 'build' : {
      \ 'windows' : 'make -f make_mingw32.mak',
      \ 'cygwin' : 'make -f make_cygwin.mak',
      \ 'mac' : 'make -f make_mac.mak',
      \ 'unix' : 'make -f make_unix.mak',
    \ },
  \ }
  NeoBundle 'Shougo/neocomplete.vim'
  NeoBundleLazy 'Shougo/vimshell', {
    \ 'depends' : 'Shougo/vimproc',
    \ 'autoload' : {
    \   'commands' : [{ 'name' : 'VimShell', 'complete' : 'customlist,vimshell#complete'},
    \                 'VimShellExecute', 'VimShellInteractive',
    \                 'VimShellTerminal', 'VimShellPop'],
    \   'mappings' : ['<Plug>(vimshell_switch)']
  \ }}
  NeoBundle 'Shougo/unite.vim'
  NeoBundle 'ujihisa/unite-colorscheme'
  NeoBundle 'Townk/vim-autoclose'
  NeoBundle 'Shougo/unite.vim'
  NeoBundle 'Shougo/neomru.vim'
  NeoBundle 'mattn/emmet-vim'
  NeoBundle 'hail2u/vim-css3-syntax'
  NeoBundle 'taichouchou2/html5.vim'
  NeoBundle 'taichouchou2/vim-javascript'
  NeoBundle 'kchmck/vim-coffee-script'
  NeoBundle 'slim-template/vim-slim'
  NeoBundle 'tpope/vim-haml'
  NeoBundle 'digitaltoad/vim-jade'
  NeoBundle 'chriskempson/vim-tomorrow-theme'
  NeoBundle 'w0ng/vim-hybrid'
  NeoBundle 'ConradIrwin/vim-bracketed-paste'
  NeoBundle 'altercation/vim-colors-solarized'
call neobundle#end()

" シンタックスハイライト
syntax on

" カラースキーム
" colorscheme Tomorrow-Night
" colorscheme hybrid
set background=dark
colorscheme solarized

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

" ペースト時にインデントさせない
" set paste

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

" emmetの設定
" Ctrl + e で展開
let g:user_emmet_expandabbr_key = '<C-e>'
" 日本語化、インデントの設定
let g:user_emmet_settings = {
  \ 'variables': {
  \   'lang': "ja"
  \ },
  \ 'indentation': '  '
\ }

" neocomplete
" Disable AutoComplPop.
let g:acp_enableAtStartup = 0
" Use neocomplete.
let g:neocomplete#enable_at_startup = 1
" Use smartcase.
let g:neocomplete#enable_smart_case = 1
" Set minimum syntax keyword length.
let g:neocomplete#sources#syntax#min_keyword_length = 3
let g:neocomplete#lock_buffer_name_pattern = '\*ku\*'

" Define dictionary.
let g:neocomplete#sources#dictionary#dictionaries = {
  \ 'default' : '',
  \ 'vimshell' : $HOME.'/.vimshell_hist',
  \ 'scheme' : $HOME.'/.gosh_completions'
    \ }

" Define keyword.
if !exists('g:neocomplete#keyword_patterns')
    let g:neocomplete#keyword_patterns = {}
endif
let g:neocomplete#keyword_patterns['default'] = '\h\w*'

" Plugin key-mappings.
inoremap <expr><C-g>     neocomplete#undo_completion()
inoremap <expr><C-l>     neocomplete#complete_common_string()

" Recommended key-mappings.
" <CR>: close popup and save indent.
inoremap <silent> <CR> <C-r>=<SID>my_cr_function()<CR>
function! s:my_cr_function()
  return neocomplete#close_popup() . "\<CR>"
  " For no inserting <CR> key.
  "return pumvisible() ? neocomplete#close_popup() : "\<CR>"
endfunction
" <TAB>: completion.
inoremap <expr><TAB>  pumvisible() ? "\<C-n>" : "\<TAB>"
" <C-h>, <BS>: close popup and delete backword char.
inoremap <expr><C-h> neocomplete#smart_close_popup()."\<C-h>"
inoremap <expr><BS> neocomplete#smart_close_popup()."\<C-h>"
inoremap <expr><C-y>  neocomplete#close_popup()
inoremap <expr><C-e>  neocomplete#cancel_popup()
" Close popup by <Space>.
"inoremap <expr><Space> pumvisible() ? neocomplete#close_popup() : "\<Space>"

" Enable omni completion.
autocmd FileType css setlocal omnifunc=csscomplete#CompleteCSS
autocmd FileType html,markdown setlocal omnifunc=htmlcomplete#CompleteTags
autocmd FileType javascript setlocal omnifunc=javascriptcomplete#CompleteJS
autocmd FileType python setlocal omnifunc=pythoncomplete#Complete
autocmd FileType xml setlocal omnifunc=xmlcomplete#CompleteTags

" Enable heavy omni completion.
if !exists('g:neocomplete#sources#omni#input_patterns')
  let g:neocomplete#sources#omni#input_patterns = {}
endif
"let g:neocomplete#sources#omni#input_patterns.php = '[^. \t]->\h\w*\|\h\w*::'
"let g:neocomplete#sources#omni#input_patterns.c = '[^.[:digit:] *\t]\%(\.\|->\)'
"let g:neocomplete#sources#omni#input_patterns.cpp = '[^.[:digit:] *\t]\%(\.\|->\)\|\h\w*::'
