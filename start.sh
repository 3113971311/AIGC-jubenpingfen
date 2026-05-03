#!/bin/bash
set -e

cd backend

echo "[start.sh] Restoring database from object storage..."
PYTHONPATH=./packages python3 db_backup.py restore

mkdir -p /tmp/uploads
mkdir -p /tmp/email_logs
mkdir -p /tmp/pending_mails
mkdir -p /tmp/script_images
mkdir -p /tmp/scoring_results
mkdir -p /tmp/script_scores

echo "[start.sh] Initializing admin account..."
PYTHONPATH=./packages python3 init_admin.py

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."
PYTHONPATH=./packages exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info 2>&1
