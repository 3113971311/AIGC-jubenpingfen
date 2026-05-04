"""SQLite 数据库对象存储备份与恢复模块（方案 A）—— 使用 boto3 直接操作 S3"""

import os
import shutil
import sys
import threading
import time
from pathlib import Path

# 确保 packages 目录在 path 中（运行时通过 PYTHONPATH 注入）
packages_dir = Path(__file__).parent / "packages"
if str(packages_dir) not in sys.path:
    sys.path.insert(0, str(packages_dir))

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

DB_KEY = "db/script_scorer.db"
UPLOADS_PREFIX = "uploads/"
DB_PATH = Path(os.getenv("DB_PATH", "/tmp/script_scorer.db"))
UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))


def _get_s3_client():
    """使用 boto3 创建 S3 客户端，从环境变量读取配置"""
    if boto3 is None:
        raise RuntimeError("boto3 not available")

    endpoint = os.environ.get("COZE_BUCKET_ENDPOINT_URL", "")
    if not endpoint:
        try:
            from coze_workload_identity import Client as CozeEnvClient
            coze_env_client = CozeEnvClient()
            env_vars = coze_env_client.get_project_env_vars()
            coze_env_client.close()
            for env_var in env_vars:
                if env_var.key == "COZE_BUCKET_ENDPOINT_URL":
                    endpoint = env_var.value
                    break
        except Exception:
            pass

    if not endpoint:
        raise RuntimeError("未配置存储端点：请设置 COZE_BUCKET_ENDPOINT_URL")

    access_key = os.environ.get("COZE_BUCKET_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("COZE_BUCKET_SECRET_ACCESS_KEY", "")
    region = os.environ.get("COZE_BUCKET_REGION", "")
    bucket = os.environ.get("COZE_BUCKET_NAME", "")

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    # 注入 x-storage-token 头
    def _inject_header(params, **kwargs):
        try:
            from coze_workload_identity import Client as CozeClient
            coze_client = CozeClient()
            try:
                token = coze_client.get_access_token()
            finally:
                coze_client.close()
            headers = params.setdefault("headers", {})
            headers["x-storage-token"] = token
        except Exception:
            pass

    client.meta.events.register("before-call.s3", _inject_header)
    return client, bucket


def restore_db():
    """启动时从对象存储恢复数据库到本地 /tmp"""
    try:
        client, bucket = _get_s3_client()
        if not bucket:
            print("[backup] COZE_BUCKET_NAME not set, skipping restore")
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, DB_KEY, str(DB_PATH))
        print(f"[backup] Database restored from s3://{bucket}/{DB_KEY}")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "404":
            print("[backup] No backup found in object storage, using fresh database")
        else:
            print(f"[backup] Restore failed: {e}")
    except Exception as e:
        print(f"[backup] Restore failed: {e}")


def backup_db():
    """将本地数据库上传到对象存储"""
    try:
        if not DB_PATH.exists():
            return
        client, bucket = _get_s3_client()
        if not bucket:
            return
        client.upload_file(str(DB_PATH), bucket, DB_KEY)
        print(f"[backup] Database backed up to s3://{bucket}/{DB_KEY}")
    except Exception as e:
        print(f"[backup] Backup failed: {e}")


def restore_uploads():
    """启动时恢复上传文件"""
    try:
        client, bucket = _get_s3_client()
        if not bucket:
            return
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        paginator = client.get_paginator("list_objects_v2")
        count = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=UPLOADS_PREFIX):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                rel_path = key[len(UPLOADS_PREFIX):]
                if not rel_path:
                    continue
                local_path = UPLOADS_DIR / rel_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                client.download_file(bucket, key, str(local_path))
                count += 1
        if count:
            print(f"[backup] Restored {count} uploaded files")
        else:
            print("[backup] No uploaded files to restore")
    except Exception as e:
        print(f"[backup] Uploads restore failed: {e}")


def backup_uploads():
    """备份所有上传文件到对象存储"""
    try:
        client, bucket = _get_s3_client()
        if not bucket:
            return
        count = 0
        for fpath in UPLOADS_DIR.rglob("*"):
            if fpath.is_file():
                rel_path = fpath.relative_to(UPLOADS_DIR)
                key = f"{UPLOADS_PREFIX}{rel_path}"
                client.upload_file(str(fpath), bucket, key)
                count += 1
        if count:
            print(f"[backup] Uploaded {count} files to object storage")
    except Exception as e:
        print(f"[backup] Uploads backup failed: {e}")


def _backup_loop():
    """后台线程：每 60 秒备份一次"""
    while True:
        time.sleep(60)
        backup_db()
        backup_uploads()


def start_background_backup():
    """启动后台定时备份线程（仅在 PROD 环境调用）"""
    t = threading.Thread(target=_backup_loop, daemon=True)
    t.start()
    print("[backup] Background backup thread started (interval=60s)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["restore", "backup"], nargs="?", default="restore")
    args = parser.parse_args()

    if args.command == "restore":
        restore_db()
        restore_uploads()
    elif args.command == "backup":
        backup_db()
        backup_uploads()
