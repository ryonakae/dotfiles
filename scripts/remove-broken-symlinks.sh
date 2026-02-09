#!/bin/bash

# 壊れたシンボリックリンクを見つける関数
function find_broken_symlinks() {
  local search_dir="$1"
  local max_depth="$2"

  # ディレクトリが存在しない場合は終了
  if [ ! -d "$search_dir" ]; then
    return 0
  fi

  # maxdepthオプションの設定
  local depth_option=""
  if [ -n "$max_depth" ]; then
    depth_option="-maxdepth $max_depth"
  fi

  # シンボリックリンクを検索し、参照先が存在しないものを抽出
  find "$search_dir" $depth_option -type l 2>/dev/null | while IFS= read -r link; do
    if [ ! -e "$link" ]; then
      echo "$link"
    fi
  done
}

# シンボリックリンクを削除する関数
function remove_symlinks() {
  local links=("$@")
  local removed_count=0

  for link in "${links[@]}"; do
    if [ -L "$link" ]; then
      rm "$link"
      echo "Removed: $link"
      ((removed_count++))
    fi
  done

  echo "$removed_count symlink(s) removed."
}

echo "Finding broken symlinks start..."

# dotfiles/configディレクトリのパスを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$DOTFILES_DIR/config"

echo "Filtering symlinks that point to: $CONFIG_DIR"
echo ""

# 壊れたシンボリックリンクを収集
broken_links=()

echo "Searching in ~/ (direct children only)..."
while IFS= read -r link; do
  if [ -n "$link" ]; then
    # リンク先のパスを取得（相対パスを絶対パスに解決）
    target=$(readlink "$link")
    # 相対パスの場合は絶対パスに変換
    if [[ "$target" != /* ]]; then
      target="$(cd "$(dirname "$link")" && cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")"
    fi
    # CONFIG_DIR配下を指している場合のみ追加
    if [[ "$target" == "$CONFIG_DIR"/* ]]; then
      broken_links+=("$link")
    fi
  fi
done << EOF
$(find_broken_symlinks "$HOME" 1)
EOF

if [ -d "$HOME/.config" ]; then
  echo "Searching in ~/.config (recursive)..."
  while IFS= read -r link; do
    if [ -n "$link" ]; then
      # リンク先のパスを取得（相対パスを絶対パスに解決）
      target=$(readlink "$link")
      # 相対パスの場合は絶対パスに変換
      if [[ "$target" != /* ]]; then
        target="$(cd "$(dirname "$link")" && cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")"
      fi
      # CONFIG_DIR配下を指している場合のみ追加
      if [[ "$target" == "$CONFIG_DIR"/* ]]; then
        broken_links+=("$link")
      fi
    fi
  done << EOF
$(find_broken_symlinks "$HOME/.config" "")
EOF
else
  echo "~/.config does not exist, skipping."
fi

# 結果の表示
if [ ${#broken_links[@]} -eq 0 ]; then
  echo "No broken symlinks found."
  echo "Finding broken symlinks finished."
  exit 0
fi

echo ""
echo "Found ${#broken_links[@]} broken symlink(s):"
echo "----------------------------------------"
for link in "${broken_links[@]}"; do
  echo "$link"
done
echo "----------------------------------------"
echo ""

# 削除確認
read -p "Do you want to remove these symlinks? (y/N): " answer
case "$answer" in
  [yY]|[yY][eE][sS])
    echo ""
    remove_symlinks "${broken_links[@]}"
    ;;
  *)
    echo "Cancelled."
    ;;
esac

echo "Finding broken symlinks finished."
