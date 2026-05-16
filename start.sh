#!/bin/bash
set -e

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."

cd backend

mkdir -p uploads

echo "[start.sh] Initializing admin account..."
python3 init_admin.py 2>/dev/null || echo "[start.sh] Warning: init_admin failed, continuing..."

exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info
