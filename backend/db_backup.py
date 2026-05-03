"""SQLite 数据库对象存储备份与恢复模块（方案 A）"""

import os
import shutil
import threading
import time
from pathlib import Path

from coze_coding_dev_sdk.s3 import S3SyncStorage

DB_KEY = "db/script_scorer.db"
UPLOADS_PREFIX = "uploads/"
DB_PATH = Path(os.getenv("DB_PATH", "/tmp/script_scorer.db"))
UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))


_storage = None


def _get_storage():
    global _storage
    if _storage is None:
        endpoint = os.getenv("COZE_BUCKET_ENDPOINT_URL")
        bucket = os.getenv("COZE_BUCKET_NAME")
        if not endpoint or not bucket:
            return None
        _storage = S3SyncStorage(
            endpoint_url=endpoint,
            access_key="",
            secret_key="",
            bucket_name=bucket,
            region="cn-beijing",
        )
    return _storage


def restore_db():
    """启动时从对象存储恢复数据库到 /tmp"""
    storage = _get_storage()
    if storage is None:
        print("[db_backup] No object storage env vars, skip restore")
        return False

    try:
        if storage.file_exists(file_key=DB_KEY):
            data = storage.read_file(file_key=DB_KEY)
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            DB_PATH.write_bytes(data)
            print(f"[db_backup] Restored database from {DB_KEY} -> {DB_PATH}")
            return True
        else:
            print(f"[db_backup] No backup found at {DB_KEY}, using fresh db")
            return False
    except Exception as e:
        print(f"[db_backup] Restore failed: {e}")
        return False


def backup_db():
    """将当前 /tmp 数据库备份到对象存储"""
    storage = _get_storage()
    if storage is None:
        return False

    if not DB_PATH.exists():
        return False

    try:
        with DB_PATH.open("rb") as f:
            key = storage.stream_upload_file(
                fileobj=f,
                file_name=DB_KEY,
                content_type="application/x-sqlite3",
            )
        print(f"[db_backup] Backed up database -> {key}")
        return True
    except Exception as e:
        print(f"[db_backup] Backup failed: {e}")
        return False


def backup_uploads():
    """备份 /tmp/uploads 下所有文件到对象存储"""
    storage = _get_storage()
    if storage is None:
        return False

    if not UPLOADS_DIR.exists():
        return False

    backed = 0
    for fpath in UPLOADS_DIR.rglob("*"):
        if fpath.is_file():
            rel = fpath.relative_to(UPLOADS_DIR).as_posix()
            key = f"{UPLOADS_PREFIX}{rel}"
            try:
                with fpath.open("rb") as f:
                    storage.stream_upload_file(
                        fileobj=f,
                        file_name=key,
                        content_type="application/octet-stream",
                    )
                backed += 1
            except Exception as e:
                print(f"[db_backup] Upload {rel} failed: {e}")
    if backed:
        print(f"[db_backup] Backed up {backed} upload files")
    return backed > 0


def restore_uploads():
    """从对象存储恢复 uploads 文件到 /tmp/uploads"""
    storage = _get_storage()
    if storage is None:
        return False

    try:
        result = storage.list_files(prefix=UPLOADS_PREFIX, max_keys=1000)
        keys = result.get("keys", [])
        if not keys:
            return False

        restored = 0
        for key in keys:
            rel = key[len(UPLOADS_PREFIX):] if key.startswith(UPLOADS_PREFIX) else key
            fpath = UPLOADS_DIR / rel
            fpath.parent.mkdir(parents=True, exist_ok=True)
            data = storage.read_file(file_key=key)
            fpath.write_bytes(data)
            restored += 1
        print(f"[db_backup] Restored {restored} upload files -> {UPLOADS_DIR}")
        return True
    except Exception as e:
        print(f"[db_backup] Restore uploads failed: {e}")
        return False


def _backup_loop(interval_sec: int = 60):
    """后台线程：每隔 interval_sec 秒备份一次数据库"""
    while True:
        time.sleep(interval_sec)
        backup_db()
        backup_uploads()


def start_background_backup(interval_sec: int = 60):
    """启动后台定时备份线程"""
    t = threading.Thread(target=_backup_loop, args=(interval_sec,), daemon=True)
    t.start()
    print(f"[db_backup] Background backup started (every {interval_sec}s)")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "restore":
        restore_db()
        restore_uploads()
    elif cmd == "backup":
        backup_db()
        backup_uploads()
    else:
        restore_db()
        restore_uploads()
