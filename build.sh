#!/bin/bash
set -e

# 构建后端：安装 Python 依赖到本地 packages 目录
cd backend
echo "[build.sh] Installing Python dependencies..."
python3 -m pip install --no-cache-dir --target ./packages -r requirements.txt
python3 -m pip install --no-cache-dir --target ./packages coze-coding-dev-sdk beautifulsoup4 lxml Pillow python-docx pypdf reportlab openai
cd ..

# 构建前端
cd frontend
echo "[build.sh] Installing frontend dependencies..."
pnpm install
echo "[build.sh] Building frontend..."
pnpm run build
cd ..

echo "[build.sh] Build complete."
