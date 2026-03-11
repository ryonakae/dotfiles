#!/bin/bash

# パス解決
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"

# グローバルスキル（全エージェントに共通配布）
GLOBAL_SKILLS_SOURCE="$DOTFILES_DIR/config/.agents/skills"

# エージェント固有スキル（特定エージェントにのみ配布）
# 形式: "ソース絶対パス:ターゲット絶対パス" の1対1マッピング
# グローバルスキルと異なり、エージェント専用の機能を持つスキルを個別に配布する
AGENT_SKILL_MAPPINGS=(
  "$DOTFILES_DIR/config/.claude/skills:$HOME/.claude/skills"
)

# ターゲット: 各エージェントのスキル読み込みディレクトリ
# ソース内の各スキルディレクトリが、以下すべてに symlink される
TARGET_DIRS=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.gemini/antigravity/skills"
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

# エージェント固有スキルを先に配布（同名スキルはこちらが優先される）
for mapping in "${AGENT_SKILL_MAPPINGS[@]}"; do
  source_dir="${mapping%%:*}"
  target_dir="${mapping##*:}"

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

# グローバルスキルを全ターゲットに配布（固有スキルで既にある場合はスキップ）
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

echo "Skills symlink creation finished."
