"""User & role administration API, plus activity log access."""
from flask import Blueprint, jsonify, request

from ..database import execute, query
from ..utils.audit import log_action
from ..utils.security import hash_password, permission_required

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.get("")
@permission_required("*")
def list_users():
    rows = query(
        "SELECT u.id, u.username, u.full_name, u.email, u.phone, u.is_active, "
        "u.last_login, u.language, r.name AS role, r.label AS role_label "
        "FROM users u JOIN roles r ON r.id = u.role_id ORDER BY u.username")
    return jsonify({"users": [dict(r) for r in rows]})


@bp.get("/roles")
@permission_required("*")
def list_roles():
    rows = query("SELECT * FROM roles ORDER BY id")
    return jsonify({"roles": [dict(r) for r in rows]})


@bp.post("")
@permission_required("*")
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role_id = data.get("role_id")
    if not username or len(password) < 6 or not role_id:
        return jsonify({"error": "username, role and a 6+ char password are required"}), 400
    if query("SELECT id FROM users WHERE username = ?", (username,), one=True):
        return jsonify({"error": "username already exists"}), 409
    uid = execute(
        "INSERT INTO users (username, full_name, password_hash, role_id, email, phone) "
        "VALUES (?,?,?,?,?,?)",
        (username, data.get("full_name", ""), hash_password(password), role_id,
         data.get("email", ""), data.get("phone", "")),
    )
    log_action("create_user", "user", uid, username)
    return jsonify({"id": uid}), 201


@bp.put("/<int:uid>")
@permission_required("*")
def update_user(uid):
    data = request.get_json(silent=True) or {}
    sets, params = [], []
    for field in ("full_name", "email", "phone", "role_id", "is_active"):
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])
    if data.get("password"):
        if len(data["password"]) < 6:
            return jsonify({"error": "password must be at least 6 characters"}), 400
        sets.append("password_hash = ?")
        params.append(hash_password(data["password"]))
    if not sets:
        return jsonify({"error": "nothing to update"}), 400
    params.append(uid)
    execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", params)
    log_action("update_user", "user", uid)
    return jsonify({"ok": True})


@bp.delete("/<int:uid>")
@permission_required("*")
def delete_user(uid):
    admins = query(
        "SELECT COUNT(*) AS c FROM users u JOIN roles r ON r.id=u.role_id "
        "WHERE r.name='administrator' AND u.is_active=1", one=True)["c"]
    target = query(
        "SELECT r.name AS role FROM users u JOIN roles r ON r.id=u.role_id WHERE u.id=?",
        (uid,), one=True)
    if target and target["role"] == "administrator" and admins <= 1:
        return jsonify({"error": "cannot delete the last administrator"}), 409
    execute("UPDATE users SET is_active = 0 WHERE id = ?", (uid,))
    log_action("delete_user", "user", uid)
    return jsonify({"ok": True})


@bp.get("/activity")
@permission_required("*")
def activity():
    args = request.args
    where, params = ["1=1"], []
    if args.get("user_id"):
        where.append("user_id = ?")
        params.append(args["user_id"])
    if args.get("action"):
        where.append("action = ?")
        params.append(args["action"])
    rows = query(
        f"SELECT * FROM activity_logs WHERE {' AND '.join(where)} "
        f"ORDER BY id DESC LIMIT 500", params)
    return jsonify({"logs": [dict(r) for r in rows]})
