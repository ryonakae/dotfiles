DOT_FILES=(.gitconfig .gitignore_global .bash_profile .zshrc .vimrc Brewfile)

for file in ${DOT_FILES[@]}

do
	if [ -a $HOME/$file ]; then
			echo "ファイルが存在するのでシンボリックリンクを貼りませんでした: $file"
	else
		ln -s $HOME/dotfiles/$file $HOME/$file
			echo "シンボリックリンクを貼りました: $file"
	fi
done
