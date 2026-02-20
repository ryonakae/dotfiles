#!/bin/bash

# skills ディレクトリのパス
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"

# グローバルスキル（全ターゲットに配布）
GLOBAL_SKILLS_SOURCE="$DOTFILES_DIR/config/.agents/skills"

TARGET_DIRS=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
)

# エージェント固有スキル（ソース相対パス:ターゲット絶対パス の1対1マッピング）
AGENT_SKILL_MAPPINGS=(
  ".claude/skills:$HOME/.claude/skills"
  ".gemini/skills:$HOME/.gemini/skills"
)

# スキップするファイルのリスト
SKIP_FILES=(".DS_Store")

echo "Skills symlink creation start..."

# グローバルスキルのソースディレクトリが存在するかチェック
if [ ! -d "$GLOBAL_SKILLS_SOURCE" ]; then
  echo "Error: Global skills source directory does not exist: $GLOBAL_SKILLS_SOURCE"
  exit 1
fi

echo "Global skills source: $GLOBAL_SKILLS_SOURCE"

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

# 第1段: グローバルスキルを全ターゲットに配布
for target_dir in "${TARGET_DIRS[@]}"; do
  echo "Processing target directory: $target_dir"

  if [ ! -d "$target_dir" ]; then
    mkdir -p "$target_dir"
    echo "Created target directory: $target_dir"
  fi

  find "$GLOBAL_SKILLS_SOURCE" -maxdepth 1 -mindepth 1 -type d | while read -r skill_dir; do
    create_skill_symlink "$skill_dir" "$target_dir"
  done
done

# 第2段: エージェント固有スキルを対応するターゲットに配布
for mapping in "${AGENT_SKILL_MAPPINGS[@]}"; do
  source_rel="${mapping%%:*}"
  target_dir="${mapping##*:}"
  source_dir="$DOTFILES_DIR/config/$source_rel"

  if [ ! -d "$source_dir" ]; then
    echo "Agent skills source does not exist, skipping: $source_dir"
    continue
  fi

  echo "Processing agent-specific skills: $source_dir -> $target_dir"

  if [ ! -d "$target_dir" ]; then
    mkdir -p "$target_dir"
    echo "Created target directory: $target_dir"
  fi

  find "$source_dir" -maxdepth 1 -mindepth 1 -type d | while read -r skill_dir; do
    create_skill_symlink "$skill_dir" "$target_dir"
  done
done

echo "Skills symlink creation finished."
