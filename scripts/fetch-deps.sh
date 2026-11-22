#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

git clone https://github.com/superzazu/z80.git --depth 1

mkdir -p tools
arch="$(uname -m)"
case "$arch" in
  x86_64) sdcc_arch=x86_64 ;;
  aarch64|arm64) sdcc_arch=aarch64 ;;
  *) echo "unsupported arch: $arch" >&2; exit 1 ;;
esac
mkdir -p /tmp/sdcc-dl
curl -L -o "/tmp/sdcc-dl/sdcc-4.6.0-linux-${sdcc_arch}.tar.gz" \
  "https://github.com/retropack/sdcc/releases/download/v4.6.0/sdcc-4.6.0-linux-${sdcc_arch}.tar.gz"
tar xzf "/tmp/sdcc-dl/sdcc-4.6.0-linux-${sdcc_arch}.tar.gz" -C tools
