#!/bin/bash

# config ディレクトリのパス
CONFIG_DIR="./config"

# config ディレクトリ配下のすべてのファイル・ディレクトリを処理
function create_symlinks() {
  local source_dir="$1"
  local target_dir="$2"

  # ソースディレクトリが存在しない場合は終了
  if [ ! -d "$source_dir" ]; then
    echo "Error: $source_dir does not exist."
    return 1
  fi

  # ソースディレクトリ内のすべてのアイテムを処理
  for item in "$source_dir"/*; do
    # アイテムが存在しない場合（空ディレクトリの場合）はスキップ
    if [ ! -e "$item" ]; then
      continue
    fi

    local item_name=$(basename "$item")
    local target_path="$target_dir/$item_name"

    # ディレクトリの場合は作成してから処理
    if [ -d "$item" ]; then
      mkdir -p "$target_path"
      create_symlinks "$item" "$target_path"
    else
      # ファイルの場合はシンボリックリンクを作成
      if [ -e "$target_path" ] || [ -L "$target_path" ]; then
        echo "$target_path already exists, skipping symlink creation."
      else
        # ターゲットディレクトリが存在しない場合は作成
        mkdir -p "$(dirname "$target_path")"
        ln -s "$item" "$target_path"
        echo "Created symlink: $target_path."
      fi
    fi
  done
}

echo "Symlink creation start..."

# config ディレクトリ配下のすべてのファイル・ディレクトリを $HOME にシンボリックリンク
create_symlinks "$CONFIG_DIR" "$HOME"

echo "Symlink creation finished."
