#!/bin/bash
set -e

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."

cd backend
export COZE_PROJECT_ENV=PROD
export PYTHONPATH="./packages:${PYTHONPATH:-}"

mkdir -p /tmp/uploads /tmp/logs

echo "[start.sh] Restoring database from object storage..."
python3 db_backup.py restore 2>/dev/null || echo "[start.sh] No backup found, using fresh db"

echo "[start.sh] Initializing admin account..."
python3 init_admin.py 2>/dev/null || echo "[start.sh] Warning: init_admin failed, continuing..."

exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info
