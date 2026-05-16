#!/bin/bash
set -e

echo "[build.sh] Building frontend..."
cd frontend
if ! command -v pnpm &> /dev/null; then
    npm install -g pnpm
fi
pnpm install
pnpm run build
cd ..

echo "[build.sh] Done."
