"""Supplier management API: CRUD, statements, payments, debts."""
from flask import Blueprint, g, jsonify, request

from ..database import execute, get_db, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required

bp = Blueprint("suppliers", __name__, url_prefix="/api/suppliers")

FIELDS = (
    "company_name", "contact_person", "phone1", "phone2", "whatsapp", "email",
    "website", "address", "city", "country", "tax_number", "category", "notes",
)


@bp.get("")
@login_required
def list_suppliers():
    q = (request.args.get("q") or "").strip()
    where, params = ["is_active = 1"], []
    if q:
        where.append("(company_name LIKE ? OR contact_person LIKE ? OR phone1 LIKE ?)")
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    rows = query(
        f"SELECT * FROM suppliers WHERE {' AND '.join(where)} ORDER BY company_name",
        params,
    )
    return jsonify({"suppliers": [dict(r) for r in rows]})


@bp.get("/<int:sid>")
@login_required
def get_supplier(sid):
    row = query("SELECT * FROM suppliers WHERE id = ?", (sid,), one=True)
    if not row:
        return jsonify({"error": "not found"}), 404
    purchases = query(
        "SELECT id, reference, invoice_number, total, paid, status, created_at "
        "FROM purchases WHERE supplier_id = ? ORDER BY id DESC LIMIT 100", (sid,))
    payments = query(
        "SELECT * FROM supplier_payments WHERE supplier_id = ? ORDER BY id DESC LIMIT 100", (sid,))
    return jsonify({
        "supplier": dict(row),
        "purchases": [dict(p) for p in purchases],
        "payments": [dict(p) for p in payments],
    })


@bp.post("")
@permission_required("suppliers")
def create_supplier():
    data = request.get_json(silent=True) or {}
    if not (data.get("company_name") or "").strip():
        return jsonify({"error": "company name is required"}), 400
    cols = [f for f in FIELDS if f in data]
    sid = execute(
        f"INSERT INTO suppliers ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [data[c] for c in cols],
    )
    log_action("create_supplier", "supplier", sid, data.get("company_name"))
    return jsonify({"id": sid}), 201


@bp.put("/<int:sid>")
@permission_required("suppliers")
def update_supplier(sid):
    data = request.get_json(silent=True) or {}
    cols = [f for f in FIELDS if f in data]
    if not cols:
        return jsonify({"error": "nothing to update"}), 400
    execute(
        f"UPDATE suppliers SET {', '.join(f'{c}=?' for c in cols)} WHERE id = ?",
        [data[c] for c in cols] + [sid],
    )
    log_action("update_supplier", "supplier", sid)
    return jsonify({"ok": True})


@bp.delete("/<int:sid>")
@permission_required("suppliers")
def delete_supplier(sid):
    execute("UPDATE suppliers SET is_active = 0 WHERE id = ?", (sid,))
    log_action("delete_supplier", "supplier", sid)
    return jsonify({"ok": True})


@bp.post("/<int:sid>/payment")
@permission_required("suppliers")
def add_payment(sid):
    data = request.get_json(silent=True) or {}
    amount = float(data.get("amount") or 0)
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO supplier_payments (supplier_id, amount, method, note, user_id) "
        "VALUES (?,?,?,?,?)",
        (sid, amount, data.get("method", "cash"), data.get("note", ""), g.user["id"]),
    )
    db.execute("UPDATE suppliers SET balance = balance - ? WHERE id = ?", (amount, sid))
    db.commit()
    log_action("supplier_payment", "supplier", sid, f"amount={amount}")
    return jsonify({"ok": True})


@bp.get("/debts")
@login_required
def debts():
    rows = query(
        "SELECT id, company_name, phone1, whatsapp, balance FROM suppliers "
        "WHERE is_active=1 AND balance > 0 ORDER BY balance DESC")
    total = sum(r["balance"] for r in rows)
    return jsonify({"suppliers": [dict(r) for r in rows], "total_debt": round(total, 2)})
