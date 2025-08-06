#!/bin/bash

# config ディレクトリのパス
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$DOTFILES_DIR/config"

# スキップするファイルのリスト
SKIP_FILES=(".DS_Store" "*.example")

# config ディレクトリ配下のすべてのファイル・ディレクトリを処理
function create_symlinks() {
  local source_dir="$1"
  local target_dir="$2"

  # ソースディレクトリが存在しない場合は終了
  if [ ! -d "$source_dir" ]; then
    echo "Error: $source_dir does not exist."
    return 1
  fi

  # findコマンドでファイルとディレクトリを取得
  find "$source_dir" -maxdepth 1 -mindepth 1 | while read -r item; do
    local item_name=$(basename "$item")
    local target_path="$target_dir/$item_name"

    # ディレクトリの場合は作成してから処理
    if [ -d "$item" ]; then
      mkdir -p "$target_path"
      create_symlinks "$item" "$target_path"
    else
      # スキップファイルのチェック
      skip_file=false
      for skip_pattern in "${SKIP_FILES[@]}"; do
        # ワイルドカードパターンの場合
        if [[ "$skip_pattern" == *"*"* ]]; then
          if [[ "$item_name" == $skip_pattern ]]; then
            echo "Skipping file: $item"
            skip_file=true
            break
          fi
        # 完全一致の場合
        else
          if [ "$item_name" = "$skip_pattern" ]; then
            echo "Skipping file: $item"
            skip_file=true
            break
          fi
        fi
      done

      if [ "$skip_file" = true ]; then
        continue
      fi

      # ファイルの場合はシンボリックリンクを作成
      if [ -e "$target_path" ] || [ -L "$target_path" ]; then
        echo "$target_path already exists, skipping symlink creation."
      else
        # ターゲットディレクトリが存在しない場合は作成
        mkdir -p "$(dirname "$target_path")"
        # 絶対パスでシンボリックリンクを作成
        ln -s "$(realpath "$item")" "$target_path"
        echo "Created symlink: $target_path -> $(realpath "$item")"
      fi
    fi
  done
}

echo "Symlink creation start..."

# config ディレクトリが存在するかチェック
if [ ! -d "$CONFIG_DIR" ]; then
  echo "Error: Config directory does not exist: $CONFIG_DIR"
  exit 1
fi

echo "Config directory: $CONFIG_DIR"
echo "Target directory: $HOME"

# config ディレクトリ配下のすべてのファイル・ディレクトリを $HOME にシンボリックリンク
create_symlinks "$CONFIG_DIR" "$HOME"

echo "Symlink creation finished."
