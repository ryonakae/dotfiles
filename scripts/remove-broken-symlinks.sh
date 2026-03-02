#!/bin/bash

# sh 経由や bash の posix モードで実行された場合でも、通常の Bash で再実行する
case ":${SHELLOPTS:-}:" in
  *:posix:*)
    exec bash "$0" "$@"
    ;;
esac

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

AUTO_YES=false
if [ "$1" = "-y" ] || [ "$1" = "--yes" ]; then
  AUTO_YES=true
fi

# 指定パス(自身を含む)配下のシンボリックリンクを列挙する関数
function find_symlinks() {
  local search_path="$1"

  if [ -L "$search_path" ]; then
    echo "$search_path"
    return 0
  fi

  if [ -d "$search_path" ]; then
    find "$search_path" -type l 2>/dev/null
  fi
}

# リンク先を絶対パスに解決する関数
function resolve_target_path() {
  local link="$1"
  local target

  target="$(readlink "$link")"
  if [ -z "$target" ]; then
    return 0
  fi

  if [[ "$target" == /* ]]; then
    echo "$target"
    return 0
  fi

  local link_dir
  link_dir="$(cd "$(dirname "$link")" && pwd)"
  if [ -z "$link_dir" ]; then
    return 0
  fi

  echo "$link_dir/$target"
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

search_roots=()
while IFS= read -r -d '' config_item; do
  config_name="$(basename "$config_item")"
  # findの結果に . と .. は含まれないが、安全のため除外
  if [ "$config_name" = "." ] || [ "$config_name" = ".." ]; then
    continue
  fi

  home_candidate="$HOME/$config_name"
  if [ -d "$home_candidate" ] || [ -L "$home_candidate" ]; then
    search_roots+=("$home_candidate")
  fi
done < <(find "$CONFIG_DIR" -mindepth 1 -maxdepth 1 -print0 2>/dev/null)

if [ ${#search_roots[@]} -eq 0 ]; then
  echo "No matching search roots found under ~/ for $CONFIG_DIR"
fi

for search_root in "${search_roots[@]}"; do
  display_root="${search_root/#$HOME/~}"
  echo "Searching in $display_root ..."

  while IFS= read -r link; do
    if [ -z "$link" ]; then
      continue
    fi

    target="$(resolve_target_path "$link")"
    if [ -z "$target" ]; then
      continue
    fi

    # config配下を参照し、かつリンク先実体が存在しないリンクのみ対象にする
    if [[ "$target" == "$CONFIG_DIR"/* ]] && [ ! -e "$target" ]; then
      broken_links+=("$link")
    fi
  done < <(find_symlinks "$search_root")
done

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
if [ "$AUTO_YES" = true ]; then
  remove_symlinks "${broken_links[@]}"
else
  # Kittyキーボードプロトコル(VS Code等)を一時的に無効化し、
  # readがEnterキーを正しく認識できるようにする
  printf '\033[>0u'
  printf 'Do you want to remove these symlinks? (y/N): '
  read -r answer
  printf '\033[<u'
  case "$answer" in
    [yY]|[yY][eE][sS])
      echo ""
      remove_symlinks "${broken_links[@]}"
      ;;
    *)
      echo "Cancelled."
      ;;
  esac
fi

echo "Finding broken symlinks finished."
