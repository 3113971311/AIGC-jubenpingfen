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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/script_scorer.db" if os.getenv("COZE_PROJECT_ENV") == "PROD" else "sqlite:///./script_scorer.db")

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
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads" if os.getenv("COZE_PROJECT_ENV") == "PROD" else "uploads")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
DEFAULT_MAX_CHARS = 100000  # 十万字


def _check_production_keys():
    """Startup check: warn about default secrets in production."""
    warnings = []
    for name, default in _DEV_DEFAULTS.items():
        if os.getenv(name, default) == default:
            warnings.append(name)
    if warnings:
        print(f"[WARN] Default secrets detected: {', '.join(warnings)}", file=sys.stderr)


_check_production_keys()
