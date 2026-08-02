"""Authentication: login, logout, session, password change/reset."""
import secrets

from flask import Blueprint, g, jsonify, request, session

from .database import execute, query
from .utils.audit import log_action
from .utils.security import (
    hash_password,
    login_required,
    role_permissions,
    verify_password,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _user_payload(user_row) -> dict:
    return {
        "id": user_row["id"],
        "username": user_row["username"],
        "full_name": user_row["full_name"],
        "role": user_row["role_name"],
        "role_label": user_row["role_label"],
        "permissions": role_permissions(user_row["role_permissions"]),
        "language": user_row["language"],
        "theme": user_row["theme"],
    }


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    row = query(
        "SELECT u.*, r.name AS role_name, r.label AS role_label, "
        "r.permissions AS role_permissions "
        "FROM users u JOIN roles r ON r.id = u.role_id "
        "WHERE u.username = ?",
        (username,),
        one=True,
    )
    if row is None or not row["is_active"] or not verify_password(password, row["password_hash"]):
        return jsonify({"error": "invalid credentials"}), 401

    session.clear()
    session.permanent = True
    session["user_id"] = row["id"]
    session["username"] = row["username"]
    execute("UPDATE users SET last_login = datetime('now','localtime') WHERE id = ?", (row["id"],))
    log_action("login", "user", row["id"], f"{username} logged in")
    # Opportunistic daily/weekly snapshot at the start of a shift.
    try:
        from .api.backup import maybe_auto_backup
        maybe_auto_backup()
    except Exception:  # noqa: BLE001 — backups must never block login
        pass
    return jsonify({"user": _user_payload(row)})


@bp.post("/logout")
def logout():
    if session.get("user_id"):
        log_action("logout", "user", session.get("user_id"))
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
def me():
    if not g.user:
        return jsonify({"user": None})
    u = g.user
    return jsonify({"user": {
        "id": u["id"],
        "username": u["username"],
        "full_name": u["full_name"],
        "role": u["role_name"],
        "role_label": u["role_label"],
        "permissions": u["permissions"],
        "language": u["language"],
        "theme": u["theme"],
    }})


@bp.post("/change-password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    if len(new) < 6:
        return jsonify({"error": "new password must be at least 6 characters"}), 400
    row = query("SELECT password_hash FROM users WHERE id = ?", (g.user["id"],), one=True)
    if not verify_password(current, row["password_hash"]):
        return jsonify({"error": "current password is incorrect"}), 403
    execute(
        "UPDATE users SET password_hash = ?, updated_at = datetime('now','localtime') WHERE id = ?",
        (hash_password(new), g.user["id"]),
    )
    log_action("change_password", "user", g.user["id"])
    return jsonify({"ok": True})


@bp.post("/reset-request")
def reset_request():
    """Generate an offline reset token for a username.

    In an offline deployment the token is shown to an administrator (there is
    no email server); an admin communicates it to the user or resets directly.
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    row = query("SELECT id FROM users WHERE username = ?", (username,), one=True)
    if row is None:
        # Do not reveal which usernames exist.
        return jsonify({"ok": True})
    token = secrets.token_urlsafe(9)
    execute("UPDATE users SET reset_token = ? WHERE id = ?", (token, row["id"]))
    return jsonify({"ok": True, "token": token})


@bp.post("/reset-confirm")
def reset_confirm():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    token = data.get("token") or ""
    new = data.get("new_password") or ""
    if len(new) < 6:
        return jsonify({"error": "new password must be at least 6 characters"}), 400
    row = query("SELECT id, reset_token FROM users WHERE username = ?", (username,), one=True)
    if row is None or not row["reset_token"] or row["reset_token"] != token:
        return jsonify({"error": "invalid token"}), 403
    execute(
        "UPDATE users SET password_hash = ?, reset_token = NULL WHERE id = ?",
        (hash_password(new), row["id"]),
    )
    log_action("reset_password", "user", row["id"])
    return jsonify({"ok": True})


@bp.post("/preferences")
@login_required
def preferences():
    """Persist per-user language + theme choices."""
    data = request.get_json(silent=True) or {}
    lang = data.get("language")
    theme = data.get("theme")
    if lang in ("en", "fr", "ar"):
        execute("UPDATE users SET language = ? WHERE id = ?", (lang, g.user["id"]))
    if theme in ("light", "dark"):
        execute("UPDATE users SET theme = ? WHERE id = ?", (theme, g.user["id"]))
    return jsonify({"ok": True})
