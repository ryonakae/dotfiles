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

FISH_FILES=(config.fish fish_plugins)
for file in ${FISH_FILES[@]}
do
	if [ -a $HOME/.config/fish/$file ]; then
			echo "$file が存在するのでシンボリックリンクを貼りませんでした"
	else
		ln -s $HOME/dotfiles/$file $HOME/.config/fish/$file
			echo "$file のシンボリックリンクを貼りました"
	fi
done
