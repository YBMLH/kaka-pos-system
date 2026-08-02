"""Centralized activity / audit logging."""
from flask import request, session

from ..database import execute


def log_action(action: str, entity: str = "", entity_id=None, detail: str = "") -> None:
    """Record an audited action for the current user."""
    try:
        ip = request.remote_addr or ""
    except RuntimeError:
        ip = ""
    execute(
        "INSERT INTO activity_logs (user_id, username, action, entity, entity_id, detail, ip) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            session.get("user_id"),
            session.get("username", ""),
            action,
            entity,
            entity_id,
            detail,
            ip,
        ),
    )
