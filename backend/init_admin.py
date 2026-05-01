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
        print("管理员账号已存在")
    db.close()


if __name__ == "__main__":
    init_admin()
