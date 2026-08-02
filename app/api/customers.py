"""Customer management API: CRUD, purchase history, credit, statements."""
from flask import Blueprint, g, jsonify, request

from ..database import execute, get_db, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required

bp = Blueprint("customers", __name__, url_prefix="/api/customers")

FIELDS = ("name", "phone", "address", "city", "notes")


@bp.get("")
@login_required
def list_customers():
    q = (request.args.get("q") or "").strip()
    where, params = ["is_active = 1"], []
    if q:
        where.append("(name LIKE ? OR phone LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    rows = query(
        f"SELECT * FROM customers WHERE {' AND '.join(where)} ORDER BY name LIMIT 300", params)
    return jsonify({"customers": [dict(r) for r in rows]})


@bp.get("/<int:cid>")
@login_required
def get_customer(cid):
    row = query("SELECT * FROM customers WHERE id = ?", (cid,), one=True)
    if not row:
        return jsonify({"error": "not found"}), 404
    sales = query(
        "SELECT id, receipt_no, total, paid, payment_method, status, created_at "
        "FROM sales WHERE customer_id = ? ORDER BY id DESC LIMIT 100", (cid,))
    stats = query(
        "SELECT COUNT(*) AS orders, COALESCE(SUM(total),0) AS spent "
        "FROM sales WHERE customer_id = ? AND status = 'completed'", (cid,), one=True)
    return jsonify({
        "customer": dict(row),
        "sales": [dict(s) for s in sales],
        "stats": dict(stats),
    })


@bp.post("")
@login_required
def create_customer():
    data = request.get_json(silent=True) or {}
    if not (data.get("name") or "").strip():
        return jsonify({"error": "name is required"}), 400
    cols = [f for f in FIELDS if f in data]
    cid = execute(
        f"INSERT INTO customers ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [data[c] for c in cols],
    )
    log_action("create_customer", "customer", cid, data.get("name"))
    return jsonify({"id": cid}), 201


@bp.put("/<int:cid>")
@login_required
def update_customer(cid):
    data = request.get_json(silent=True) or {}
    cols = [f for f in FIELDS if f in data]
    if not cols:
        return jsonify({"error": "nothing to update"}), 400
    execute(
        f"UPDATE customers SET {', '.join(f'{c}=?' for c in cols)} WHERE id = ?",
        [data[c] for c in cols] + [cid],
    )
    log_action("update_customer", "customer", cid)
    return jsonify({"ok": True})


@bp.delete("/<int:cid>")
@permission_required("customers")
def delete_customer(cid):
    execute("UPDATE customers SET is_active = 0 WHERE id = ?", (cid,))
    log_action("delete_customer", "customer", cid)
    return jsonify({"ok": True})


@bp.post("/<int:cid>/settle")
@login_required
def settle_credit(cid):
    """Record a payment against a customer's outstanding credit."""
    data = request.get_json(silent=True) or {}
    amount = float(data.get("amount") or 0)
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400
    db = get_db()
    db.execute("UPDATE customers SET credit = MAX(credit - ?, 0) WHERE id = ?", (amount, cid))
    db.commit()
    log_action("customer_settle", "customer", cid, f"amount={amount}")
    return jsonify({"ok": True})
