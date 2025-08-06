#!/bin/bash

echo "Install start..."

# XCode Command Line Toolsのインストール
if ! xcode-select --print-path &> /dev/null; then
  echo "Command Line Tools not found. Installing..."
  xcode-select --install
else
  echo "Command Line Tools is already installed."
fi

# Homebrewのインストール
if ! command -v brew &> /dev/null; then
  echo "Homebrew not found. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "Homebrew is already installed."
fi

echo "Install finished."
