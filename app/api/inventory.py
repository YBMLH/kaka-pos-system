"""Inventory API: adjustments, damage/loss/expiry, movements, alerts, count sessions."""
from flask import Blueprint, g, jsonify, request

from ..database import get_db, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required
from ..utils.stock import adjust_stock

bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

ADJUST_REASONS = {"adjustment", "damage", "loss", "expired", "transfer", "count"}


@bp.post("/adjust")
@permission_required("inventory")
def adjust():
    """Apply a manual stock change. ``mode='set'`` sets an absolute quantity,
    otherwise ``change`` is added/subtracted."""
    data = request.get_json(silent=True) or {}
    pid = data.get("product_id")
    reason = data.get("reason", "adjustment")
    if reason not in ADJUST_REASONS:
        return jsonify({"error": "invalid reason"}), 400
    db = get_db()
    prod = db.execute("SELECT quantity, name_en FROM products WHERE id = ?", (pid,)).fetchone()
    if not prod:
        return jsonify({"error": "product not found"}), 404

    if data.get("mode") == "set":
        target = float(data.get("quantity") or 0)
        change = target - (prod["quantity"] or 0)
    else:
        change = float(data.get("change") or 0)
    balance = adjust_stock(db, pid, change, reason, "manual", None, note=data.get("note", ""))
    db.commit()
    log_action("inventory_adjust", "product", pid,
               f"{reason} {change:+g} -> {balance} ({prod['name_en']})")
    return jsonify({"ok": True, "balance": balance})


@bp.get("/movements")
@login_required
def movements():
    args = request.args
    where, params = ["1=1"], []
    if args.get("product_id"):
        where.append("m.product_id = ?")
        params.append(args["product_id"])
    if args.get("reason"):
        where.append("m.reason = ?")
        params.append(args["reason"])
    if args.get("date_from"):
        where.append("date(m.created_at) >= ?")
        params.append(args["date_from"])
    if args.get("date_to"):
        where.append("date(m.created_at) <= ?")
        params.append(args["date_to"])
    rows = query(
        f"SELECT m.*, p.name_en AS product_name, u.username FROM inventory_movements m "
        f"LEFT JOIN products p ON p.id = m.product_id "
        f"LEFT JOIN users u ON u.id = m.user_id "
        f"WHERE {' AND '.join(where)} ORDER BY m.id DESC LIMIT 500",
        params,
    )
    return jsonify({"movements": [dict(r) for r in rows]})


@bp.get("/alerts")
@login_required
def alerts():
    low = query(
        "SELECT id, name_en, barcode, quantity, min_stock, unit FROM products "
        "WHERE is_archived=0 AND quantity <= min_stock AND min_stock > 0 "
        "ORDER BY quantity ASC LIMIT 200"
    )
    out_of_stock = query(
        "SELECT id, name_en, barcode, quantity FROM products "
        "WHERE is_archived=0 AND quantity <= 0 ORDER BY name_en LIMIT 200"
    )
    expiring = query(
        "SELECT id, name_en, barcode, quantity, expiry_date FROM products "
        "WHERE is_archived=0 AND expiry_date IS NOT NULL AND expiry_date != '' "
        "AND date(expiry_date) <= date('now','localtime','+30 day') "
        "ORDER BY expiry_date ASC LIMIT 200"
    )
    return jsonify({
        "low_stock": [dict(r) for r in low],
        "out_of_stock": [dict(r) for r in out_of_stock],
        "expiring": [dict(r) for r in expiring],
    })


@bp.get("/value")
@login_required
def inventory_value():
    row = query(
        "SELECT COALESCE(SUM(quantity*purchase_price),0) AS cost_value, "
        "COALESCE(SUM(quantity*selling_price),0) AS retail_value, "
        "COALESCE(SUM(quantity),0) AS total_units, COUNT(*) AS products "
        "FROM products WHERE is_archived=0", one=True,
    )
    return jsonify(dict(row))


@bp.post("/count-session")
@permission_required("inventory")
def count_session():
    """Reconcile a physical count. ``counts`` = [{product_id, counted}]."""
    data = request.get_json(silent=True) or {}
    counts = data.get("counts") or []
    db = get_db()
    adjusted = 0
    for c in counts:
        pid = c.get("product_id")
        counted = float(c.get("counted") or 0)
        prod = db.execute("SELECT quantity FROM products WHERE id=?", (pid,)).fetchone()
        if not prod:
            continue
        diff = counted - (prod["quantity"] or 0)
        if diff != 0:
            adjust_stock(db, pid, diff, "count", "count_session", None,
                         note=f"Physical count reconciliation ({diff:+g})")
            adjusted += 1
    db.commit()
    log_action("inventory_count", detail=f"{adjusted} products reconciled")
    return jsonify({"ok": True, "adjusted": adjusted})
