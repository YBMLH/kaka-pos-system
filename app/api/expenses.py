"""Expense management API."""
from flask import Blueprint, g, jsonify, request

from ..database import execute, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required

bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")

CATEGORIES = ["Rent", "Electricity", "Water", "Gas", "Internet", "Salaries",
              "Fuel", "Maintenance", "Supplies", "Miscellaneous"]


@bp.get("/categories")
@login_required
def categories():
    return jsonify({"categories": CATEGORIES})


@bp.get("")
@login_required
def list_expenses():
    args = request.args
    where, params = ["1=1"], []
    if args.get("category"):
        where.append("e.category = ?")
        params.append(args["category"])
    if args.get("date_from"):
        where.append("e.spent_on >= ?")
        params.append(args["date_from"])
    if args.get("date_to"):
        where.append("e.spent_on <= ?")
        params.append(args["date_to"])
    rows = query(
        f"SELECT e.*, u.username FROM expenses e LEFT JOIN users u ON u.id = e.user_id "
        f"WHERE {' AND '.join(where)} ORDER BY e.spent_on DESC, e.id DESC LIMIT 500", params)
    total = query(
        f"SELECT COALESCE(SUM(amount),0) AS t FROM expenses e WHERE {' AND '.join(where)}",
        params, one=True)["t"]
    return jsonify({"expenses": [dict(r) for r in rows], "total": round(total, 2)})


@bp.post("")
@permission_required("expenses")
def create_expense():
    data = request.get_json(silent=True) or {}
    amount = float(data.get("amount") or 0)
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400
    spent_on = data.get("spent_on") or None
    if spent_on:
        eid = execute(
            "INSERT INTO expenses (category, amount, note, user_id, spent_on) VALUES (?,?,?,?,?)",
            (data.get("category", "Miscellaneous"), amount, data.get("note", ""),
             g.user["id"], spent_on),
        )
    else:
        # Let the column default (today's local date) apply.
        eid = execute(
            "INSERT INTO expenses (category, amount, note, user_id) VALUES (?,?,?,?)",
            (data.get("category", "Miscellaneous"), amount, data.get("note", ""), g.user["id"]),
        )
    log_action("create_expense", "expense", eid, f"{data.get('category')} {amount}")
    return jsonify({"id": eid}), 201


@bp.put("/<int:eid>")
@permission_required("expenses")
def update_expense(eid):
    data = request.get_json(silent=True) or {}
    execute(
        "UPDATE expenses SET category=?, amount=?, note=?, "
        "spent_on=COALESCE(NULLIF(?, ''), spent_on) WHERE id=?",
        (data.get("category", "Miscellaneous"), float(data.get("amount") or 0),
         data.get("note", ""), data.get("spent_on") or "", eid),
    )
    log_action("update_expense", "expense", eid)
    return jsonify({"ok": True})


@bp.delete("/<int:eid>")
@permission_required("expenses")
def delete_expense(eid):
    execute("DELETE FROM expenses WHERE id = ?", (eid,))
    log_action("delete_expense", "expense", eid)
    return jsonify({"ok": True})


@bp.get("/monthly")
@login_required
def monthly_report():
    rows = query(
        "SELECT strftime('%Y-%m', spent_on) AS month, category, SUM(amount) AS total "
        "FROM expenses GROUP BY month, category ORDER BY month DESC")
    return jsonify({"rows": [dict(r) for r in rows]})
