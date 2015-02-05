caskroom="/usr/local/Caskroom"
apps=($(brew cask list))
for a in ${apps[@]};do
  info=$(brew cask info $a)
  if echo "$info"| grep -q "Not installed";then
    brew cask install $a
  fi
  current=$(echo "$info"|grep "${caskroom}/${a}"|cut -d' ' -f1)
  for dir in $(ls ${caskroom}/${a});do
    testdir="${caskroom}/${a}/${dir}"
    if [ "$testdir" != "$current" ];then
      rm -rf "$testdir"
    fi
  done
done