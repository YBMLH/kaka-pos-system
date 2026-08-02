"""Store settings API + logo upload."""
import os
import time

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from ..database import execute, get_db, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required

bp = Blueprint("settings", __name__, url_prefix="/api/settings")

ALLOWED_IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


@bp.get("")
@login_required
def get_settings():
    rows = query("SELECT key, value FROM settings")
    return jsonify({"settings": {r["key"]: r["value"] for r in rows}})


@bp.put("")
@permission_required("settings")
def update_settings():
    data = request.get_json(silent=True) or {}
    db = get_db()
    for key, value in data.items():
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
    db.commit()
    log_action("update_settings", "settings", detail=",".join(data.keys()))
    return jsonify({"ok": True})


@bp.post("/logo")
@permission_required("settings")
def upload_logo():
    file = request.files.get("logo")
    if not file or not file.filename:
        return jsonify({"error": "no file"}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMG:
        return jsonify({"error": "unsupported image type"}), 400
    fname = secure_filename(f"logo_{int(time.time())}{ext}")
    path = os.path.join(current_app.config["UPLOAD_DIR"], fname)
    file.save(path)
    rel = f"/static/uploads/{fname}"
    execute(
        "INSERT INTO settings (key, value) VALUES ('store_logo', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (rel,))
    log_action("upload_logo", "settings")
    return jsonify({"ok": True, "path": rel})
