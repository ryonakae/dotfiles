#!/bin/bash

# パス解決
SCRIPT_PATH="$0"
case "$SCRIPT_PATH" in
  /*) ;;
  *) SCRIPT_PATH="$PWD/$SCRIPT_PATH" ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)
DOTFILES_DIR=$(dirname "$SCRIPT_DIR")

# グローバルスキル（全エージェントに共通配布）
GLOBAL_SKILLS_SOURCE="$DOTFILES_DIR/config/.agents/skills"

# エージェント固有スキル（特定エージェントにのみ配布）
# 形式: "ソース絶対パス:ターゲット絶対パス" の1対1マッピング
# グローバルスキルと異なり、エージェント専用の機能を持つスキルを個別に配布する
AGENT_SKILL_MAPPINGS=$(cat <<EOF
$DOTFILES_DIR/config/.claude/skills:$HOME/.claude/skills
EOF
)

# ターゲット: 各エージェントのスキル読み込みディレクトリ
# ソース内の各スキルディレクトリが、以下すべてに symlink される
TARGET_DIRS=$(cat <<EOF
$HOME/.agents/skills
$HOME/.claude/skills
$HOME/.gemini/antigravity/skills
EOF
)

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

create_skill_symlink() (
  skill_dir="$1"
  target_dir="$2"
  skill_name=$(basename "$skill_dir")
  target_path="$target_dir/$skill_name"

  # スキップファイルのチェック
  case "$skill_name" in
    .DS_Store)
      return
      ;;
  esac

  # シンボリックリンクを作成
  if [ -e "$target_path" ] || [ -L "$target_path" ]; then
    add_skipped_link "$target_path"
    return
  fi

  source_path=$(realpath "$skill_dir")
  ln -s "$source_path" "$target_path"
  add_created_link "$target_path" "$source_path"
)

trap cleanup_temp_files EXIT HUP INT TERM

echo "Skills symlink creation start..."

# グローバルスキルのソースディレクトリが存在するかチェック
if [ ! -d "$GLOBAL_SKILLS_SOURCE" ]; then
  echo "Error: Global skills source directory does not exist: $GLOBAL_SKILLS_SOURCE"
  exit 1
fi

echo "Global skills source: $GLOBAL_SKILLS_SOURCE"

# エージェント固有スキルを先に配布（同名スキルはこちらが優先される）
printf '%s\n' "$AGENT_SKILL_MAPPINGS" | while IFS= read -r mapping; do
  [ -n "$mapping" ] || continue

  source_dir=${mapping%%:*}
  target_dir=${mapping##*:}

  if [ ! -d "$source_dir" ]; then
    echo "Agent skills source does not exist, skipping: $source_dir"
    continue
  fi

  if [ ! -d "$target_dir" ]; then
    mkdir -p "$target_dir"
  fi

  find "$source_dir" -maxdepth 1 -mindepth 1 -type d | while IFS= read -r skill_dir; do
    create_skill_symlink "$skill_dir" "$target_dir"
  done
done

# グローバルスキルを全ターゲットに配布（固有スキルで既にある場合はスキップ）
printf '%s\n' "$TARGET_DIRS" | while IFS= read -r target_dir; do
  [ -n "$target_dir" ] || continue

  if [ ! -d "$target_dir" ]; then
    mkdir -p "$target_dir"
  fi

  find "$GLOBAL_SKILLS_SOURCE" -maxdepth 1 -mindepth 1 -type d | while IFS= read -r skill_dir; do
    create_skill_symlink "$skill_dir" "$target_dir"
  done
done

print_summary

echo "Skills symlink creation finished."
