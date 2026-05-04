#!/bin/bash
set -e

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."

cd backend
export COZE_PROJECT_ENV=PROD
export PYTHONPATH="./packages:${PYTHONPATH:-}"

mkdir -p /tmp/uploads /tmp/logs

exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info
