#!/bin/bash

# skills ディレクトリのパス
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_SOURCE_DIR="$DOTFILES_DIR/config/.agents/skills"

# ターゲットディレクトリのリスト
TARGET_DIRS=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.gemini/skills"
)

# スキップするファイルのリスト
SKIP_FILES=(".DS_Store")

echo "Skills symlink creation start..."

# ソースディレクトリが存在するかチェック
if [ ! -d "$SKILLS_SOURCE_DIR" ]; then
  echo "Error: Skills source directory does not exist: $SKILLS_SOURCE_DIR"
  exit 1
fi

echo "Skills source directory: $SKILLS_SOURCE_DIR"

# シンボリックリンク作成関数
create_skill_symlink() {
  local skill_dir="$1"
  local target_dir="$2"
  local skill_name
  skill_name=$(basename "$skill_dir")
  local target_path="$target_dir/$skill_name"

  # スキップファイルのチェック
  for skip_pattern in "${SKIP_FILES[@]}"; do
    if [ "$skill_name" = "$skip_pattern" ]; then
      echo "Skipping: $skill_name"
      return
    fi
  done

  # シンボリックリンクを作成
  if [ -e "$target_path" ] || [ -L "$target_path" ]; then
    echo "$target_path already exists, skipping symlink creation."
  else
    ln -s "$(realpath "$skill_dir")" "$target_path"
    echo "Created symlink: $target_path -> $(realpath "$skill_dir")"
  fi
}

# 各ターゲットディレクトリに対してシンボリックリンクを作成
for target_dir in "${TARGET_DIRS[@]}"; do
  echo "Processing target directory: $target_dir"

  # ターゲットディレクトリが存在しない場合は作成
  if [ ! -d "$target_dir" ]; then
    mkdir -p "$target_dir"
    echo "Created target directory: $target_dir"
  fi

  # skills ディレクトリ配下の各ディレクトリをシンボリックリンク
  find "$SKILLS_SOURCE_DIR" -maxdepth 1 -mindepth 1 -type d | while read -r skill_dir; do
    create_skill_symlink "$skill_dir" "$target_dir"
  done
done

echo "Skills symlink creation finished."
