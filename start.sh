#!/bin/bash
set -e

cd backend

# 确保 packages 存在，若不存在则运行时安装
if [ ! -d "./packages" ] || [ -z "$(ls -A ./packages 2>/dev/null)" ]; then
    echo "[start.sh] packages not found, installing dependencies..."
    python3 -m pip install --no-cache-dir --target ./packages -r requirements.txt
fi

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."
PYTHONPATH=./packages python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000
