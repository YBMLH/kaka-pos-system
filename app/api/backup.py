"""Backup & restore API — safe SQLite snapshots with checksum verification."""
import hashlib
import os
import shutil
import sqlite3
import time
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_file

from ..database import execute, get_db, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required

bp = Blueprint("backup", __name__, url_prefix="/api/backup")


def _checksum(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def create_backup(kind: str = "manual") -> dict:
    """Create a consistent snapshot using SQLite's online backup API."""
    src_path = current_app.config["DATABASE"]
    backup_dir = current_app.config["BACKUP_DIR"]
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"kaka_{kind}_{stamp}.db"
    dest = os.path.join(backup_dir, fname)

    # Online backup guarantees a consistent copy even while the DB is in use.
    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dest)
    with dst:
        src.backup(dst)
    dst.close()
    src.close()

    checksum = _checksum(dest)
    size = os.path.getsize(dest)
    execute(
        "INSERT INTO backups (filename, size_bytes, kind, checksum, verified) VALUES (?,?,?,?,1)",
        (fname, size, kind, checksum),
    )
    return {"filename": fname, "size_bytes": size, "kind": kind, "checksum": checksum}


def maybe_auto_backup() -> None:
    """Create daily/weekly backups if the newest one is stale. Cheap to call."""
    setting = query("SELECT value FROM settings WHERE key='auto_backup'", one=True)
    if not setting or setting["value"] != "1":
        return
    last_daily = query(
        "SELECT created_at FROM backups WHERE kind='daily' ORDER BY id DESC LIMIT 1", one=True)
    today = datetime.now().strftime("%Y-%m-%d")
    if not last_daily or not str(last_daily["created_at"]).startswith(today):
        create_backup("daily")
    last_weekly = query(
        "SELECT created_at FROM backups WHERE kind='weekly' ORDER BY id DESC LIMIT 1", one=True)
    if not last_weekly or (time.time() - _age(last_weekly["created_at"])) > 7 * 86400:
        create_backup("weekly")


def _age(ts_str) -> float:
    try:
        return time.mktime(datetime.strptime(str(ts_str), "%Y-%m-%d %H:%M:%S").timetuple())
    except ValueError:
        return 0


@bp.get("")
@permission_required("settings")
def list_backups():
    rows = query("SELECT * FROM backups ORDER BY id DESC LIMIT 200")
    return jsonify({"backups": [dict(r) for r in rows]})


@bp.post("/create")
@permission_required("settings")
def manual_backup():
    info = create_backup("manual")
    log_action("backup_create", "backup", detail=info["filename"])
    return jsonify(info), 201


@bp.get("/download/<int:bid>")
@permission_required("settings")
def download_backup(bid):
    row = query("SELECT * FROM backups WHERE id = ?", (bid,), one=True)
    if not row:
        return jsonify({"error": "not found"}), 404
    path = os.path.join(current_app.config["BACKUP_DIR"], row["filename"])
    if not os.path.exists(path):
        return jsonify({"error": "file missing"}), 404
    return send_file(path, as_attachment=True, download_name=row["filename"])


@bp.post("/verify/<int:bid>")
@permission_required("settings")
def verify_backup(bid):
    row = query("SELECT * FROM backups WHERE id = ?", (bid,), one=True)
    if not row:
        return jsonify({"error": "not found"}), 404
    path = os.path.join(current_app.config["BACKUP_DIR"], row["filename"])
    if not os.path.exists(path):
        execute("UPDATE backups SET verified = 0 WHERE id = ?", (bid,))
        return jsonify({"ok": False, "reason": "file missing"})
    ok = _checksum(path) == row["checksum"]
    # Confirm the snapshot opens and passes an integrity check.
    if ok:
        try:
            conn = sqlite3.connect(path)
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            conn.close()
            ok = result == "ok"
        except sqlite3.Error:
            ok = False
    execute("UPDATE backups SET verified = ? WHERE id = ?", (1 if ok else 0, bid))
    return jsonify({"ok": ok})


@bp.post("/restore/<int:bid>")
@permission_required("*")
def restore_backup(bid):
    row = query("SELECT * FROM backups WHERE id = ?", (bid,), one=True)
    if not row:
        return jsonify({"error": "not found"}), 404
    path = os.path.join(current_app.config["BACKUP_DIR"], row["filename"])
    if not os.path.exists(path):
        return jsonify({"error": "backup file missing"}), 404
    if _checksum(path) != row["checksum"]:
        return jsonify({"error": "checksum mismatch — backup may be corrupt"}), 409

    # Snapshot the current DB first so a bad restore is reversible.
    create_backup("pre-restore")
    db_path = current_app.config["DATABASE"]
    # Close the request connection and checkpoint WAL before replacing the file.
    get_db().execute("PRAGMA wal_checkpoint(TRUNCATE)")
    get_db().close()
    for suffix in ("-wal", "-shm"):
        stale = db_path + suffix
        if os.path.exists(stale):
            os.remove(stale)
    shutil.copy2(path, db_path)
    log_action("backup_restore", "backup", bid, row["filename"])
    return jsonify({"ok": True, "restored": row["filename"],
                    "note": "Restart the application to load the restored database."})


@bp.post("/upload")
@permission_required("*")
def upload_backup():
    """Import an external .db backup file into the backup registry."""
    file = request.files.get("file")
    if not file or not file.filename.endswith(".db"):
        return jsonify({"error": "a .db backup file is required"}), 400
    fname = f"kaka_uploaded_{int(time.time())}.db"
    dest = os.path.join(current_app.config["BACKUP_DIR"], fname)
    file.save(dest)
    try:
        conn = sqlite3.connect(dest)
        conn.execute("PRAGMA integrity_check")
        conn.close()
    except sqlite3.Error:
        os.remove(dest)
        return jsonify({"error": "not a valid SQLite database"}), 400
    checksum = _checksum(dest)
    bid = execute(
        "INSERT INTO backups (filename, size_bytes, kind, checksum, verified) VALUES (?,?,?,?,1)",
        (fname, os.path.getsize(dest), "uploaded", checksum),
    )
    return jsonify({"id": bid, "filename": fname}), 201
