#!/bin/bash
set -e

# 通过 PYTHONPATH 加载本地 packages 目录中的依赖，启动后端服务
cd backend
PYTHONPATH=./packages python3 -m uvicorn deploy_app:app --host :: --port 5000
