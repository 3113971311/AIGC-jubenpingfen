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

echo "[build.sh] Installing Python dependencies to ./packages..."
cd backend
python3 -m pip install --no-cache-dir --target ./packages -r requirements.txt
cd ..

echo "[build.sh] Done."
