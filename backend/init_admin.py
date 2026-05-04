"""初始化管理员账号"""
from database import init_db, SessionLocal
from models import User
from auth import hash_password


def init_admin():
    init_db()
    db = SessionLocal()
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            points=9999,
            is_admin=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("管理员账号已创建: admin / admin123")
    else:
        # 每次启动重置密码，确保不会因为恢复旧数据库导致密码错误
        existing.password_hash = hash_password("admin123")
        existing.is_admin = True
        existing.is_active = True
        db.commit()
        print("管理员账号密码已重置: admin / admin123")
    db.close()


if __name__ == "__main__":
    init_admin()
