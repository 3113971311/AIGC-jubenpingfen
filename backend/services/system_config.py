from sqlalchemy.orm import Session

from models import SystemConfig


def get_config(db: Session, key: str, default: str = "") -> str:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row else default


def get_config_int(db: Session, key: str, default: int = 0) -> int:
    try:
        return int(get_config(db, key, str(default)))
    except ValueError:
        return default


def set_config(db: Session, key: str, value: str):
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(SystemConfig(key=key, value=value))
    db.commit()


def get_all_configs(db: Session) -> dict:
    rows = db.query(SystemConfig).all()
    return {r.key: r.value for r in rows}
