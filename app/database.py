"""SQLite connection management and one-time initialization.

Uses a per-request connection stored on Flask's ``g``. Enables WAL mode for
concurrent reads during writes and sets pragmatic performance pragmas suited
to large local datasets.
"""
import json
import os
import sqlite3

from flask import current_app, g

from .config import Config
from .utils.security import hash_password
from .utils.text import build_search_blob  # noqa: F401 (re-exported for convenience)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

DEFAULT_ROLES = [
    ("administrator", "Administrator", ["*"]),
    ("manager", "Manager", [
        "dashboard", "pos", "products.view", "products.edit", "inventory",
        "suppliers", "customers", "purchases", "expenses", "reports",
        "register", "zakat", "settings", "edit_price", "refund", "discount",
    ]),
    ("cashier", "Cashier", [
        "dashboard", "pos", "products.view", "customers", "register",
        "discount", "refund",
    ]),
    ("inventory", "Inventory Employee", [
        "dashboard", "products.view", "products.edit", "inventory",
        "suppliers", "purchases",
    ]),
]

DEFAULT_SETTINGS = {
    "store_name": "KAKA Market",
    "store_address": "",
    "store_phone": "",
    "store_logo": "",
    "currency": Config.DEFAULT_CURRENCY,
    "tax_rate": str(Config.DEFAULT_TAX_RATE),
    "language": Config.DEFAULT_LANGUAGE,
    "receipt_width": "80",          # 58 or 80 mm
    "receipt_footer": "Thank you for your visit!",
    "zakat_rate": str(Config.ZAKAT_RATE),
    "low_stock_alerts": "1",
    "auto_backup": "1",
}


def get_db() -> sqlite3.Connection:
    """Return the request-scoped database connection, opening it if needed."""
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=30,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA cache_size = -16000")  # ~16 MB page cache
        g.db = conn
    return g.db


def close_db(exception=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql: str, params=(), one: bool = False):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql: str, params=()) -> int:
    """Run a write statement and return the last row id."""
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id


def init_db() -> None:
    """Create schema, seed roles/settings and the default admin if missing."""
    db = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        db.executescript(fh.read())
    db.commit()

    # Roles
    for name, label, perms in DEFAULT_ROLES:
        db.execute(
            "INSERT OR IGNORE INTO roles (name, label, permissions) VALUES (?,?,?)",
            (name, label, json.dumps(perms)),
        )
    db.commit()

    # Default settings
    for key, val in DEFAULT_SETTINGS.items():
        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", (key, val))
    db.commit()

    # Default administrator (username: admin / password: admin123)
    existing = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    if existing["c"] == 0:
        admin_role = db.execute(
            "SELECT id FROM roles WHERE name = 'administrator'"
        ).fetchone()
        db.execute(
            "INSERT INTO users (username, full_name, password_hash, role_id) "
            "VALUES (?,?,?,?)",
            ("admin", "System Administrator", hash_password("admin123"), admin_role["id"]),
        )
        db.commit()
