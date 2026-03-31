#!/bin/bash

# config ディレクトリのパス
SCRIPT_PATH="$0"
case "$SCRIPT_PATH" in
  /*) ;;
  *) SCRIPT_PATH="$PWD/$SCRIPT_PATH" ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)
DOTFILES_DIR=$(dirname "$SCRIPT_DIR")
CONFIG_DIR="$DOTFILES_DIR/config"

# 作成結果を最後にまとめて表示する
CREATED_LINKS_FILE=$(mktemp)
SKIPPED_LINKS_FILE=$(mktemp)

cleanup_temp_files() {
  rm -f "$CREATED_LINKS_FILE" "$SKIPPED_LINKS_FILE"
}

add_created_link() {
  target_path="$1"
  source_path="$2"
  printf '%s\n' "$target_path -> $source_path" >> "$CREATED_LINKS_FILE"
}

add_skipped_link() {
  target_path="$1"
  printf '%s\n' "$target_path" >> "$SKIPPED_LINKS_FILE"
}

print_link_list() {
  title="$1"
  list_file="$2"

  echo
  echo "$title"

  if [ ! -s "$list_file" ]; then
    echo "なし"
    return
  fi

  while IFS= read -r entry; do
    echo "- $entry"
  done < "$list_file"
}

print_summary() {
  print_link_list "新規で作成したシンボリックリンク一覧" "$CREATED_LINKS_FILE"
  print_link_list "スキップしたシンボリックリンク一覧" "$SKIPPED_LINKS_FILE"
}

# config ディレクトリ配下のすべてのファイル・ディレクトリを処理
create_symlinks() (
  source_dir="$1"
  target_dir="$2"
  parent_path="$3"  # config からの相対パス

  # ソースディレクトリが存在しない場合は終了
  if [ ! -d "$source_dir" ]; then
    echo "Error: $source_dir does not exist."
    return 1
  fi

  # findコマンドでファイルとディレクトリを取得
  find "$source_dir" -maxdepth 1 -mindepth 1 | while IFS= read -r item; do
    item_name=$(basename "$item")
    target_path="$target_dir/$item_name"
    current_path="${parent_path:+$parent_path/}$item_name"

    # ディレクトリの場合
    if [ -d "$item" ]; then
      # skills ディレクトリはスキップ
      if [ "$item_name" = "skills" ]; then
        continue
      fi

      # 通常のディレクトリは作成してから再帰的に処理
      mkdir -p "$target_path"
      create_symlinks "$item" "$target_path" "$current_path"
      continue
    fi

    # スキップファイルのチェック
    case "$item_name" in
      .DS_Store|*.example)
        continue
        ;;
    esac

    # ファイルの場合はシンボリックリンクを作成
    if [ -e "$target_path" ] || [ -L "$target_path" ]; then
      add_skipped_link "$target_path"
      continue
    fi

    source_path=$(realpath "$item")

    # ターゲットディレクトリが存在しない場合は作成
    mkdir -p "$(dirname "$target_path")"
    # 絶対パスでシンボリックリンクを作成
    ln -s "$source_path" "$target_path"
    add_created_link "$target_path" "$source_path"
  done
)

trap cleanup_temp_files EXIT HUP INT TERM

echo "Symlink creation start..."

# config ディレクトリが存在するかチェック
if [ ! -d "$CONFIG_DIR" ]; then
  echo "Error: Config directory does not exist: $CONFIG_DIR"
  exit 1
fi

echo "Config directory: $CONFIG_DIR"
echo "Target directory: $HOME"

# config ディレクトリ配下のすべてのファイル・ディレクトリを $HOME にシンボリックリンク
create_symlinks "$CONFIG_DIR" "$HOME" ""

print_summary

echo "Symlink creation finished."
