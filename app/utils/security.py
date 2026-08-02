"""Password hashing and permission helpers.

Passwords use Werkzeug's PBKDF2-SHA256 which is salted and slow enough to
resist offline brute force while requiring no external dependency.
"""
import functools
import json

from flask import g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def current_user():
    return getattr(g, "user", None)


def has_permission(permission: str) -> bool:
    user = current_user()
    if not user:
        return False
    perms = user.get("permissions") or []
    return "*" in perms or permission in perms


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "authentication required"}), 401
        return view(*args, **kwargs)
    return wrapped


def permission_required(permission: str):
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return jsonify({"error": "authentication required"}), 401
            if not has_permission(permission):
                return jsonify({"error": "permission denied", "need": permission}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


def role_permissions(permissions_json: str):
    try:
        return json.loads(permissions_json or "[]")
    except (ValueError, TypeError):
        return []
