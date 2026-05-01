import os
import secrets
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

_DEV_DEFAULTS = {
    "JWT_SECRET_KEY": "change-me-to-a-random-string-in-production",
    "ENCRYPTION_KEY": "change-me-32-bytes-key-here!!",
}

# JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEV_DEFAULTS["JWT_SECRET_KEY"])
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2  # 2 hours (reduced from 7 days)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./script_scorer.db")

# Encryption key for API keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", _DEV_DEFAULTS["ENCRYPTION_KEY"])

# SMTP (for feedback emails)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
FEEDBACK_RECIPIENT = os.getenv("FEEDBACK_RECIPIENT", "3113971311@qq.com")

# File upload
UPLOAD_DIR = "uploads"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
DEFAULT_MAX_CHARS = 100000  # 十万字


def _check_production_keys():
    """Startup check: refuse to run with default secrets in production."""
    warnings = []
    for name, default in _DEV_DEFAULTS.items():
        if os.getenv(name, default) == default:
            warnings.append(name)
    if warnings:
        # Generate a usable random key so the dev experience isn't blocked
        hint = secrets.token_urlsafe(32)
        sys.stderr.write(
            "\n"
            "=" * 60 + "\n"
            "  SECURITY WARNING: 以下密钥使用了默认值，生产环境必须修改:\n"
            f"  {', '.join(warnings)}\n\n"
            "  设置环境变量:\n"
            f"  export JWT_SECRET_KEY={hint}\n"
            f"  export ENCRYPTION_KEY={secrets.token_urlsafe(32)}\n"
            "=" * 60 + "\n\n"
        )


_check_production_keys()
