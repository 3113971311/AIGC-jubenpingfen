#!/bin/bash
set -e

# 构建后端：将 Python 依赖安装到本地 packages 目录
# 使用 --target 确保依赖随项目打包到 veFaaS 运行时
cd backend
pip install --no-cache-dir --target ./packages -r requirements.txt
cd ..

# 构建前端
cd frontend
pnpm install
pnpm run build
cd ..
