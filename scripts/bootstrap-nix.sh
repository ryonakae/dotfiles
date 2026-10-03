#!/bin/bash
set -euo pipefail

if [[ $# != 1 || $1 != --install ]]; then
  printf '%s\n' 'Usage: bash scripts/bootstrap-nix.sh --install' >&2
  exit 2
fi

if [[ ${APP_SANDBOX_CONTAINER_ID:-} == agent-safehouse ]]; then
  printf '%s\n' 'error: run the Nix installer in a human terminal outside Safehouse.' >&2
  exit 1
fi

if [[ $(uname -s) != Darwin || $(uname -m) != arm64 ]]; then
  printf '%s\n' 'error: this bootstrap supports Apple Silicon macOS only.' >&2
  exit 1
fi

if command -v nix >/dev/null 2>&1; then
  printf '%s\n' 'Nix is already on PATH; no installation was performed. Verify the existing installation before migration.'
  exit 0
fi

for existing in /nix /etc/nix /Library/LaunchDaemons/org.nixos.nix-daemon.plist /usr/local/bin/determinate-nixd; do
  if stat -f '%N' "$existing" >/dev/null 2>&1; then
    printf 'error: existing Nix path requires manual inspection: %s\n' "$existing" >&2
    exit 1
  fi
done

version=2.34.0
sha256=47cb78c9fdc7b630dbbb9a89869c8e8bcd8c9eb17be036fba18585120693a4c1
archive="nix-$version-aarch64-darwin.tar.xz"
url="https://releases.nixos.org/nix/nix-$version/$archive"
work=$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-nix.XXXXXXXX")
trap '/bin/rm -rf -- "$work"' EXIT

curl --fail --location --proto '=https' --tlsv1.2 --output "$work/$archive" "$url"
printf '%s  %s\n' "$sha256" "$work/$archive" | shasum -a 256 --check
/usr/bin/tar -xJf "$work/$archive" -C "$work" --strip-components=1
/bin/sh "$work/install" --daemon --no-channel-add
