"""Application configuration.

All settings default to values suitable for a single-store offline deployment.
Override via environment variables when needed (e.g. a stronger SECRET_KEY in
production, set once and stored on the local machine).
"""
import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
UPLOAD_DIR = os.path.join(BASE_DIR, "app", "static", "uploads")

for _d in (INSTANCE_DIR, BACKUP_DIR, UPLOAD_DIR):
    os.makedirs(_d, exist_ok=True)

# Persist a generated secret key so sessions survive restarts on the same box.
_SECRET_FILE = os.path.join(INSTANCE_DIR, "secret.key")
if os.environ.get("SECRET_KEY"):
    _SECRET = os.environ["SECRET_KEY"]
elif os.path.exists(_SECRET_FILE):
    with open(_SECRET_FILE, "r", encoding="utf-8") as fh:
        _SECRET = fh.read().strip()
else:
    _SECRET = secrets.token_hex(32)
    with open(_SECRET_FILE, "w", encoding="utf-8") as fh:
        fh.write(_SECRET)


class Config:
    SECRET_KEY = _SECRET
    DATABASE = os.environ.get("KAKA_DB", os.path.join(INSTANCE_DIR, "kaka_pos.db"))
    BACKUP_DIR = BACKUP_DIR
    UPLOAD_DIR = UPLOAD_DIR
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB uploads (images / imports)

    # Session lasts a full working shift; refreshed on every request.
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 12
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Default business settings (editable from the Settings screen).
    DEFAULT_CURRENCY = "MAD"
    DEFAULT_TAX_RATE = 20.0
    DEFAULT_LANGUAGE = "en"
    ZAKAT_RATE = 2.5
