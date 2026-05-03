#!/bin/bash
set -e

cd backend

echo "[start.sh] Restoring database from object storage..."
PYTHONPATH=./packages python3 -c "
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_backup import restore_db, restore_uploads
restore_db()
restore_uploads()
"

echo "[start.sh] Initializing admin account..."
PYTHONPATH=./packages python3 init_admin.py

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."
PYTHONPATH=./packages exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info 2>&1
