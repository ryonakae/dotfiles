#!/bin/sh

echo "Start Homebrew maintenance..."

echo "\nUpdate"
brew update

echo "\nUpgrade Homebrew"
brew upgrade

echo "\nUpgrade Homebrew Cask"
brew cask upgrade

echo "\nCleanup"
brew cleanup
brew cask cleanup

echo "\nCheck Homebrew"
brew doctor

echo "\nFinish."