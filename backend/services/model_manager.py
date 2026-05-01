import base64
import hashlib

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from config import ENCRYPTION_KEY
from models import ModelConfig


def _get_cipher() -> Fernet:
    """Derive a 32-byte Fernet key from ENCRYPTION_KEY using SHA-256."""
    raw = ENCRYPTION_KEY.encode("utf-8")
    derived = hashlib.sha256(raw).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def encrypt_api_key(plain_text: str) -> str:
    return _get_cipher().encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_api_key(encrypted: str) -> str:
    return _get_cipher().decrypt(encrypted.encode("utf-8")).decode("utf-8")


def mask_api_key(key: str) -> str:
    try:
        decrypted = decrypt_api_key(key)
    except Exception:
        # Logged at debug level in production; fall back to all-masked
        return "****"
    if not decrypted:
        return "****"
    if len(decrypted) <= 8:
        return decrypted[:2] + "****" + decrypted[-2:]
    return decrypted[:4] + "****" + decrypted[-4:]


def get_active_models(db: Session):
    return db.query(ModelConfig).filter(ModelConfig.is_active == True).all()  # noqa: E712


def get_model_config(db: Session, model_id: int) -> ModelConfig | None:
    return db.query(ModelConfig).filter(ModelConfig.id == model_id).first()


def create_model_config(db: Session, provider: str, model_name: str,
                        api_base: str, api_key: str) -> ModelConfig:
    model = ModelConfig(
        provider=provider,
        model_name=model_name,
        api_base=api_base.rstrip("/"),
        api_key=encrypt_api_key(api_key),
        is_active=True,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_model_config(db: Session, model_id: int, **kwargs) -> ModelConfig | None:
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        return None
    if "api_key" in kwargs and kwargs["api_key"]:
        kwargs["api_key"] = encrypt_api_key(kwargs["api_key"])
    if "api_base" in kwargs and kwargs["api_base"]:
        kwargs["api_base"] = kwargs["api_base"].rstrip("/")
    for key, value in kwargs.items():
        if value is not None and hasattr(model, key):
            setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model


def delete_model_config(db: Session, model_id: int) -> bool:
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        return False
    db.delete(model)
    db.commit()
    return True


def toggle_model_config(db: Session, model_id: int) -> ModelConfig | None:
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        return None
    model.is_active = not model.is_active
    db.commit()
    db.refresh(model)
    return model
