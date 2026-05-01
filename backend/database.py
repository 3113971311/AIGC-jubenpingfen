from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # SQLite 兼容迁移：为已有 scores 表添加 progress 列
    with engine.connect() as conn:
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(scores);").fetchall()]
        if "progress" not in cols:
            conn.exec_driver_sql("ALTER TABLE scores ADD COLUMN progress VARCHAR(500) DEFAULT '';")
            conn.commit()

    # 设置系统默认配置
    from models import SystemConfig
    db = SessionLocal()
    defaults = {"max_chars": "100000", "points_per_10000_chars": "1", "active_model_id": "", "score_timeout": "300"}
    for k, v in defaults.items():
        if not db.query(SystemConfig).filter(SystemConfig.key == k).first():
            db.add(SystemConfig(key=k, value=v))
    db.commit()
    db.close()
