#!/bin/bash

# mosh-server を macOS Application Firewall の着信許可に登録する。
#
# Homebrew の mosh-server は未署名かつ読み取り専用のため、ALF が許可登録時に
# 打ち込む ad-hoc 署名を書き込めず、--listapps 上は許可に見えても実際の UDP
# 着信は落とされる。そこで先に自前で ad-hoc 署名してから登録し直す。
# バージョン番号を含む実体パスが brew upgrade のたびに変わるので、
# 更新後はこのスクリプトを再実行する。

set -euo pipefail

SOCKETFILTERFW=/usr/libexec/ApplicationFirewall/socketfilterfw

# mosh-server の実体パス(symlink を解決したもの)を取得する関数
function resolve_mosh_server() {
  local link
  link="$(command -v mosh-server)" || return 1

  # ALF はバージョン番号を含む実体パス単位で判定するため symlink を解決する
  readlink -f "$link"
}

# 読み取り専用のバイナリに ad-hoc 署名を打ち込む関数
function sign_adhoc() {
  local binary="$1"
  local mode
  mode="$(stat -f '%Lp' "$binary")"

  sudo chmod u+w "$binary"
  sudo codesign --force --sign - "$binary"
  sudo chmod "$mode" "$binary"
}

# 登録済みの古い mosh-server エントリを削除する関数
function remove_stale_entries() {
  local current="$1"

  "$SOCKETFILTERFW" --listapps \
    | grep -oE '/[^ ]*/mosh-server' \
    | sort -u \
    | while read -r entry; do
        if [ "$entry" != "$current" ]; then
          echo "Removing stale entry: $entry"
          sudo "$SOCKETFILTERFW" --remove "$entry" > /dev/null
        fi
      done
}

echo "Allow mosh-server on firewall start..."

if ! MOSH_SERVER="$(resolve_mosh_server)"; then
  echo "mosh-server not found. Install it with 'brew install mosh'."
  exit 1
fi

echo "Target: $MOSH_SERVER"

sign_adhoc "$MOSH_SERVER"
remove_stale_entries "$MOSH_SERVER"

# 既存エントリを消してから入れ直し、署名し直した実体を確実に反映させる
sudo "$SOCKETFILTERFW" --remove "$MOSH_SERVER" > /dev/null 2>&1 || true
sudo "$SOCKETFILTERFW" --add "$MOSH_SERVER" > /dev/null
sudo "$SOCKETFILTERFW" --unblockapp "$MOSH_SERVER" > /dev/null

echo "Done."
"$SOCKETFILTERFW" --getappblocked "$MOSH_SERVER"
