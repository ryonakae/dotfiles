apps=($(brew cask list))
for a in ${apps[@]};do
  if grep -q "Not installed" < <(brew cask info $a);then
    brew cask install $a
  fi
done