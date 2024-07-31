# $HOME直下に置くファイル
DOT_FILES=(.zshrc .vimrc .hyper.js)
for file in ${DOT_FILES[@]}
do
  if [ -a $HOME/$file ]; then
    echo "$file が存在するのでシンボリックリンクを貼りませんでした"
  else
    ln -s $HOME/dotfiles/$file $HOME/$file
    echo "$file のシンボリックリンクを貼りました"
  fi
done

# fishの設定ファイル
mkdir -p $HOME/.config/fish
FISH_FILES=(.config/fish/config.fish .config/fish/fish_plugins)
for file in ${FISH_FILES[@]}
do
  if [ -a $HOME/$file ]; then
    echo "$file が存在するのでシンボリックリンクを貼りませんでした"
  else
    ln -s $HOME/dotfiles/$file $HOME/$file
    echo "$file のシンボリックリンクを貼りました"
  fi
done

# huskyの設定ファイル
mkdir -p $HOME/.config/husky
HUSKY_FILE=.config/husky/init.sh
if [ -a $HOME/$HUSKY_FILE ]; then
  echo "$HUSKY_FILE が存在するのでシンボリックリンクを貼りませんでした"
else
  ln -s $HOME/dotfiles/$HUSKY_FILE $HOME/$HUSKY_FILE
  echo "$HUSKY_FILE のシンボリックリンクを貼りました"
fi
