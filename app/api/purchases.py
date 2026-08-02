"""Purchase orders API: draft/order/receive, returns, and automatic reordering."""
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from ..database import get_db, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required
from ..utils.stock import adjust_stock

bp = Blueprint("purchases", __name__, url_prefix="/api/purchases")


def _next_reference(db) -> str:
    today = datetime.now().strftime("%Y%m%d")
    c = db.execute("SELECT COUNT(*) AS c FROM purchases WHERE reference LIKE ?",
                   (f"PO{today}%",)).fetchone()["c"]
    return f"PO{today}-{c + 1:04d}"


@bp.get("")
@login_required
def list_purchases():
    args = request.args
    where, params = ["1=1"], []
    if args.get("status"):
        where.append("p.status = ?")
        params.append(args["status"])
    if args.get("supplier_id"):
        where.append("p.supplier_id = ?")
        params.append(args["supplier_id"])
    rows = query(
        f"SELECT p.*, s.company_name AS supplier_name FROM purchases p "
        f"LEFT JOIN suppliers s ON s.id = p.supplier_id "
        f"WHERE {' AND '.join(where)} ORDER BY p.id DESC LIMIT 300", params)
    return jsonify({"purchases": [dict(r) for r in rows]})


@bp.get("/<int:pid>")
@login_required
def get_purchase(pid):
    p = query(
        "SELECT p.*, s.company_name AS supplier_name FROM purchases p "
        "LEFT JOIN suppliers s ON s.id=p.supplier_id WHERE p.id=?", (pid,), one=True)
    if not p:
        return jsonify({"error": "not found"}), 404
    items = query("SELECT * FROM purchase_items WHERE purchase_id = ?", (pid,))
    d = dict(p)
    d["items"] = [dict(i) for i in items]
    return jsonify({"purchase": d})


@bp.post("")
@permission_required("purchases")
def create_purchase():
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    if not items:
        return jsonify({"error": "no items"}), 400
    db = get_db()
    subtotal = sum(float(i.get("quantity", 0)) * float(i.get("cost", 0)) for i in items)
    reference = _next_reference(db)
    cur = db.execute(
        "INSERT INTO purchases (reference, supplier_id, user_id, invoice_number, "
        "subtotal, total, status, note) VALUES (?,?,?,?,?,?,?,?)",
        (reference, data.get("supplier_id") or None, g.user["id"],
         data.get("invoice_number", ""), round(subtotal, 2), round(subtotal, 2),
         data.get("status", "draft"), data.get("note", "")),
    )
    pid = cur.lastrowid
    for it in items:
        qty = float(it.get("quantity", 0))
        cost = float(it.get("cost", 0))
        db.execute(
            "INSERT INTO purchase_items (purchase_id, product_id, name, quantity, cost, line_total) "
            "VALUES (?,?,?,?,?,?)",
            (pid, it.get("product_id"), it.get("name", ""), qty, cost, round(qty * cost, 2)),
        )
    db.commit()
    log_action("create_purchase", "purchase", pid, reference)
    return jsonify({"id": pid, "reference": reference}), 201


@bp.post("/<int:pid>/receive")
@permission_required("purchases")
def receive_purchase(pid):
    """Receive stock (full or partial). ``items`` = [{purchase_item_id, received}].
    When omitted, receives the full outstanding quantity of every line."""
    purchase = query("SELECT * FROM purchases WHERE id = ?", (pid,), one=True)
    if not purchase:
        return jsonify({"error": "not found"}), 404
    if purchase["status"] in ("received", "cancelled"):
        return jsonify({"error": f"purchase already {purchase['status']}"}), 409

    data = request.get_json(silent=True) or {}
    req = {int(i["purchase_item_id"]): float(i["received"]) for i in (data.get("items") or [])}
    db = get_db()
    lines = db.execute("SELECT * FROM purchase_items WHERE purchase_id = ?", (pid,)).fetchall()

    for line in lines:
        outstanding = line["quantity"] - line["received_qty"]
        recv = req.get(line["id"], outstanding) if req else outstanding
        recv = min(max(recv, 0), outstanding)
        if recv <= 0:
            continue
        db.execute("UPDATE purchase_items SET received_qty = received_qty + ? WHERE id = ?",
                   (recv, line["id"]))
        if line["product_id"]:
            adjust_stock(db, line["product_id"], recv, "purchase", "purchase", pid,
                         note=purchase["reference"])
            # Keep cost price in sync with the latest purchase cost.
            db.execute("UPDATE products SET purchase_price = ? WHERE id = ?",
                       (line["cost"], line["product_id"]))

    remaining = db.execute(
        "SELECT SUM(quantity - received_qty) AS r FROM purchase_items WHERE purchase_id = ?",
        (pid,)).fetchone()["r"] or 0
    status = "received" if remaining <= 0 else "partial"
    db.execute("UPDATE purchases SET status = ? WHERE id = ?", (status, pid))
    # Increase supplier balance (we now owe them for received goods).
    if purchase["supplier_id"]:
        db.execute("UPDATE suppliers SET balance = balance + ? WHERE id = ?",
                   (purchase["total"] - purchase["paid"], purchase["supplier_id"]))
    db.commit()
    log_action("receive_purchase", "purchase", pid, f"{purchase['reference']} status={status}")
    return jsonify({"ok": True, "status": status})


@bp.post("/<int:pid>/status")
@permission_required("purchases")
def set_status(pid):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("draft", "ordered", "cancelled"):
        return jsonify({"error": "invalid status"}), 400
    db = get_db()
    db.execute("UPDATE purchases SET status = ? WHERE id = ?", (status, pid))
    db.commit()
    return jsonify({"ok": True})


@bp.get("/reorder-suggestions")
@login_required
def reorder_suggestions():
    """Products at/below minimum stock, grouped by supplier, with reorder qty
    and supplier contact info — ready to become draft purchase orders."""
    rows = query(
        "SELECT p.id, p.name_en, p.barcode, p.quantity, p.min_stock, p.purchase_price, "
        "p.supplier_id, s.company_name, s.phone1, s.whatsapp, s.email "
        "FROM products p LEFT JOIN suppliers s ON s.id = p.supplier_id "
        "WHERE p.is_archived=0 AND p.min_stock > 0 AND p.quantity <= p.min_stock "
        "ORDER BY s.company_name, p.name_en")
    groups = {}
    for r in rows:
        key = r["supplier_id"] or 0
        g_ = groups.setdefault(key, {
            "supplier_id": r["supplier_id"],
            "supplier_name": r["company_name"] or "Unassigned",
            "phone": r["phone1"], "whatsapp": r["whatsapp"], "email": r["email"],
            "items": [],
        })
        # Reorder up to double the minimum as a sensible default buffer.
        reorder_qty = max(r["min_stock"] * 2 - r["quantity"], r["min_stock"])
        g_["items"].append({
            "product_id": r["id"], "name": r["name_en"], "barcode": r["barcode"],
            "quantity": r["quantity"], "min_stock": r["min_stock"],
            "reorder_qty": round(reorder_qty, 2), "cost": r["purchase_price"],
        })
    return jsonify({"groups": list(groups.values())})


@bp.post("/generate-reorders")
@permission_required("purchases")
def generate_reorders():
    """Create draft purchase orders from the reorder suggestions, one per supplier."""
    resp = reorder_suggestions()
    groups = resp.get_json()["groups"]
    db = get_db()
    created = []
    for grp in groups:
        if not grp["supplier_id"]:
            continue
        items = grp["items"]
        subtotal = sum(i["reorder_qty"] * (i["cost"] or 0) for i in items)
        reference = _next_reference(db)
        cur = db.execute(
            "INSERT INTO purchases (reference, supplier_id, user_id, subtotal, total, status, note) "
            "VALUES (?,?,?,?,?,?,?)",
            (reference, grp["supplier_id"], g.user["id"], round(subtotal, 2),
             round(subtotal, 2), "draft", "Auto-generated reorder"),
        )
        pid = cur.lastrowid
        for i in items:
            db.execute(
                "INSERT INTO purchase_items (purchase_id, product_id, name, quantity, cost, line_total) "
                "VALUES (?,?,?,?,?,?)",
                (pid, i["product_id"], i["name"], i["reorder_qty"], i["cost"] or 0,
                 round(i["reorder_qty"] * (i["cost"] or 0), 2)),
            )
        created.append({"id": pid, "reference": reference, "supplier": grp["supplier_name"]})
    db.commit()
    log_action("generate_reorders", "purchase", detail=f"{len(created)} orders")
    return jsonify({"created": created})
