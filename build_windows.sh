#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
SRC="$ROOT_DIR/src/screenshot.cpp"
OUT_DIR="$ROOT_DIR/dist"
OUT="$OUT_DIR/screenshot.exe"

if ! command -v x86_64-w64-mingw32-g++ >/dev/null 2>&1; then
  echo "x86_64-w64-mingw32-g++ not found. On Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y mingw-w64" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

x86_64-w64-mingw32-g++ -std=c++17 -O2 -s -municode -o "$OUT" "$SRC" -lgdiplus -lgdi32

echo "Built $OUT"
