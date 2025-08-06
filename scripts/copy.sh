#!/bin/bash

# dotfiles ディレクトリのパス
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"

# .example ファイルを探して同じディレクトリにコピーする関数
function copy_example_files() {
  local base_dir="$1"

  # .example ファイルを再帰的に検索
  find "$base_dir" -name "*.example" -type f | while read -r example_file; do
    # .example を除いたファイル名を生成
    local target_file="${example_file%.example}"

    # ターゲットファイルが既に存在する場合はスキップ
    if [ -e "$target_file" ]; then
      echo "$(basename "$target_file") already exists, skipping copy."
    else
      # .example ファイルをコピー
      cp "$example_file" "$target_file"
      echo "Copied $(basename "$example_file") to $(basename "$target_file")."
    fi
  done
}

echo "Copy examples start..."

# dotfiles ディレクトリ以下の .example ファイルをコピー
copy_example_files "$DOTFILES_DIR"

echo "Copy examples finished."
