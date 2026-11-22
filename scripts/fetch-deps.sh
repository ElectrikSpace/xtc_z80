#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

gh repo clone superzazu/z80 github__superzazu__z80 -- --depth 1

mkdir -p tools
arch="$(uname -m)"
case "$arch" in
  x86_64) sdcc_arch=x86_64 ;;
  aarch64|arm64) sdcc_arch=aarch64 ;;
  *) echo "unsupported arch: $arch" >&2; exit 1 ;;
esac
gh release download v4.6.0 --repo retropack/sdcc \
  --pattern "sdcc-4.6.0-linux-${sdcc_arch}.tar.gz" --dir /tmp/sdcc-dl
tar xzf "/tmp/sdcc-dl/sdcc-4.6.0-linux-${sdcc_arch}.tar.gz" -C tools
