#!/bin/bash
set -e

cd backend

# 构建阶段已将 requirements.txt 安装到 ./packages（只读但可导入）
export PYTHONPATH="./packages:${PYTHONPATH:-}"

echo "[start.sh] PYTHONPATH: $PYTHONPATH"

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
