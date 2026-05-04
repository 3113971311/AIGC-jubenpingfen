#!/bin/bash
set -e

cd backend

echo "[start.sh] Installing runtime dependencies..."
python3 -m pip install --no-cache-dir \
  coze-coding-dev-sdk beautifulsoup4 lxml Pillow python-docx pypdf reportlab openai 2>&1 | tail -3 || {
    echo "[start.sh] Warning: pip install returned non-zero, continuing..."
}

echo "[start.sh] Restoring database from object storage..."
python3 db_backup.py restore || {
    echo "[start.sh] Warning: db_backup restore failed, continuing with fresh db..."
}

mkdir -p /tmp/uploads
mkdir -p /tmp/email_logs
mkdir -p /tmp/pending_mails
mkdir -p /tmp/script_images
mkdir -p /tmp/scoring_results
mkdir -p /tmp/script_scores

echo "[start.sh] Initializing admin account..."
python3 init_admin.py || {
    echo "[start.sh] Warning: init_admin failed, continuing..."
}

echo "[start.sh] Starting uvicorn on 0.0.0.0:5000..."
exec python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info 2>&1
