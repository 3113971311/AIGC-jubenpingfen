#!/bin/bash
set -e

cd backend

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."
PYTHONPATH=./packages exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info 2>&1
