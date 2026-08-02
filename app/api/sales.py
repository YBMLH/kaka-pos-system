"""Sales / POS API: checkout, hold & resume, refunds, receipts, history."""
import io
import json
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from ..database import get_db, query
from ..utils.audit import log_action
from ..utils.security import has_permission, login_required, permission_required
from ..utils.stock import adjust_stock

bp = Blueprint("sales", __name__, url_prefix="/api/sales")


def _next_receipt_no(db) -> str:
    today = datetime.now().strftime("%Y%m%d")
    row = db.execute(
        "SELECT COUNT(*) AS c FROM sales WHERE receipt_no LIKE ?", (f"R{today}%",)
    ).fetchone()
    return f"R{today}-{row['c'] + 1:04d}"


@bp.post("/checkout")
@permission_required("pos")
def checkout():
    """Finalize a sale. Validates stock, records the sale + items, updates stock,
    customer credit and loyalty, all in one transaction."""
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    if not items:
        return jsonify({"error": "cart is empty"}), 400

    payment_method = data.get("payment_method", "cash")
    order_discount = float(data.get("discount") or 0)
    customer_id = data.get("customer_id") or None
    paid = float(data.get("paid") or 0)
    payment_detail = data.get("payment_detail") or {}

    db = get_db()
    subtotal = tax_total = cost_total = 0.0
    prepared = []

    for it in items:
        pid = it.get("product_id")
        qty = float(it.get("quantity") or 0)
        if qty <= 0:
            continue
        prod = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if prod is None:
            return jsonify({"error": f"product {pid} not found"}), 400
        if qty > (prod["quantity"] or 0):
            return jsonify({
                "error": "insufficient stock",
                "product": prod["name_en"],
                "available": prod["quantity"],
            }), 409

        unit_price = float(it.get("unit_price", prod["selling_price"]))
        # Only privileged users may override the price below/above the catalog.
        if unit_price != float(prod["selling_price"]) and not has_permission("edit_price"):
            unit_price = float(prod["selling_price"])
        line_discount = float(it.get("discount") or 0)
        tax_rate = float(prod["tax_rate"] or 0)
        gross = unit_price * qty - line_discount
        line_tax = gross * tax_rate / 100.0
        line_cost = float(prod["purchase_price"] or 0) * qty

        subtotal += gross
        tax_total += line_tax
        cost_total += line_cost
        prepared.append({
            "product_id": pid, "name": prod["name_en"] or prod["name_ar"],
            "barcode": prod["barcode"] or "", "quantity": qty,
            "unit_price": unit_price, "purchase_price": float(prod["purchase_price"] or 0),
            "discount": line_discount, "tax_rate": tax_rate,
            "line_total": round(gross + line_tax, 2),
        })

    if not prepared:
        return jsonify({"error": "no valid items"}), 400

    total = round(subtotal - order_discount + tax_total, 2)
    profit = round(subtotal - order_discount - cost_total, 2)
    if payment_method == "credit":
        paid = paid or 0
    change_due = round(max(paid - total, 0), 2)

    receipt_no = _next_receipt_no(db)
    register = db.execute(
        "SELECT id FROM registers WHERE status='open' AND user_id=? ORDER BY id DESC LIMIT 1",
        (g.user["id"],),
    ).fetchone()

    cur = db.execute(
        "INSERT INTO sales (receipt_no, user_id, customer_id, register_id, subtotal, "
        "discount, tax, total, cost_total, profit, paid, change_due, payment_method, "
        "payment_detail, status, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (receipt_no, g.user["id"], customer_id, register["id"] if register else None,
         round(subtotal, 2), order_discount, round(tax_total, 2), total,
         round(cost_total, 2), profit, paid, change_due, payment_method,
         json.dumps(payment_detail), "completed", data.get("note", "")),
    )
    sale_id = cur.lastrowid

    for p in prepared:
        db.execute(
            "INSERT INTO sale_items (sale_id, product_id, name, barcode, quantity, "
            "unit_price, purchase_price, discount, tax_rate, line_total) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (sale_id, p["product_id"], p["name"], p["barcode"], p["quantity"],
             p["unit_price"], p["purchase_price"], p["discount"], p["tax_rate"],
             p["line_total"]),
        )
        adjust_stock(db, p["product_id"], -p["quantity"], "sale", "sale", sale_id,
                     note=receipt_no)

    # Customer credit + loyalty (1 point per currency unit of total, floor).
    if customer_id:
        if payment_method == "credit":
            outstanding = total - paid
            db.execute("UPDATE customers SET credit = credit + ? WHERE id = ?",
                       (outstanding, customer_id))
        db.execute("UPDATE customers SET loyalty_pts = loyalty_pts + ? WHERE id = ?",
                   (int(total), customer_id))

    db.commit()
    log_action("sale", "sale", sale_id, f"{receipt_no} total={total}")
    return jsonify({"sale_id": sale_id, "receipt_no": receipt_no, "total": total,
                    "change_due": change_due, "profit": profit}), 201


@bp.get("")
@login_required
def list_sales():
    args = request.args
    page = max(int(args.get("page", 1)), 1)
    per_page = min(int(args.get("per_page", 50)), 200)
    where, params = ["1=1"], []
    if args.get("status"):
        where.append("s.status = ?")
        params.append(args["status"])
    if args.get("date_from"):
        where.append("date(s.created_at) >= ?")
        params.append(args["date_from"])
    if args.get("date_to"):
        where.append("date(s.created_at) <= ?")
        params.append(args["date_to"])
    if args.get("user_id"):
        where.append("s.user_id = ?")
        params.append(args["user_id"])
    if args.get("q"):
        where.append("s.receipt_no LIKE ?")
        params.append(f"%{args['q']}%")
    where_sql = " AND ".join(where)
    total = query(f"SELECT COUNT(*) AS c FROM sales s WHERE {where_sql}", params, one=True)["c"]
    rows = query(
        f"SELECT s.*, u.username AS cashier, c.name AS customer_name FROM sales s "
        f"LEFT JOIN users u ON u.id = s.user_id "
        f"LEFT JOIN customers c ON c.id = s.customer_id "
        f"WHERE {where_sql} ORDER BY s.id DESC LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page],
    )
    return jsonify({"sales": [dict(r) for r in rows], "total": total, "page": page,
                    "pages": (total + per_page - 1) // per_page})


@bp.get("/<int:sid>")
@login_required
def get_sale(sid):
    sale = query(
        "SELECT s.*, u.username AS cashier, c.name AS customer_name, c.phone AS customer_phone "
        "FROM sales s LEFT JOIN users u ON u.id=s.user_id "
        "LEFT JOIN customers c ON c.id=s.customer_id WHERE s.id=?",
        (sid,), one=True,
    )
    if not sale:
        return jsonify({"error": "not found"}), 404
    items = query("SELECT * FROM sale_items WHERE sale_id = ?", (sid,))
    data = dict(sale)
    data["items"] = [dict(i) for i in items]
    try:
        data["payment_detail"] = json.loads(sale["payment_detail"] or "{}")
    except ValueError:
        data["payment_detail"] = {}
    return jsonify({"sale": data})


@bp.post("/<int:sid>/refund")
@permission_required("refund")
def refund_sale(sid):
    """Full or partial refund. ``items`` = [{sale_item_id, quantity}]; empty = full."""
    sale = query("SELECT * FROM sales WHERE id = ?", (sid,), one=True)
    if not sale:
        return jsonify({"error": "not found"}), 404
    if sale["status"] == "refunded":
        return jsonify({"error": "already refunded"}), 409

    data = request.get_json(silent=True) or {}
    req_items = data.get("items")
    db = get_db()
    lines = db.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sid,)).fetchall()

    refund_amount = 0.0
    full = not req_items
    req_map = {int(i["sale_item_id"]): float(i["quantity"]) for i in (req_items or [])}

    for line in lines:
        qty = line["quantity"] - line["refunded_qty"] if full else req_map.get(line["id"], 0)
        qty = min(qty, line["quantity"] - line["refunded_qty"])
        if qty <= 0:
            continue
        proportion = qty / line["quantity"] if line["quantity"] else 0
        refund_amount += line["line_total"] * proportion
        db.execute("UPDATE sale_items SET refunded_qty = refunded_qty + ? WHERE id = ?",
                   (qty, line["id"]))
        if line["product_id"]:
            adjust_stock(db, line["product_id"], qty, "return", "refund", sid,
                         note=f"Refund {sale['receipt_no']}")

    remaining = db.execute(
        "SELECT SUM(quantity - refunded_qty) AS r FROM sale_items WHERE sale_id = ?", (sid,)
    ).fetchone()["r"] or 0
    new_status = "refunded" if remaining <= 0 else "partial_refund"
    db.execute("UPDATE sales SET status = ? WHERE id = ?", (new_status, sid))
    db.commit()
    log_action("refund", "sale", sid, f"{sale['receipt_no']} amount={round(refund_amount,2)}")
    return jsonify({"ok": True, "refunded": round(refund_amount, 2), "status": new_status})


# ---- Hold / resume ---------------------------------------------------------
@bp.post("/hold")
@permission_required("pos")
def hold_sale():
    data = request.get_json(silent=True) or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO held_sales (label, user_id, cart_json) VALUES (?,?,?)",
        (data.get("label", ""), g.user["id"], json.dumps(data.get("cart") or {})),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid}), 201


@bp.get("/held")
@permission_required("pos")
def list_held():
    rows = query("SELECT * FROM held_sales ORDER BY id DESC")
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["cart"] = json.loads(r["cart_json"])
        except ValueError:
            d["cart"] = {}
        out.append(d)
    return jsonify({"held": out})


@bp.delete("/held/<int:hid>")
@permission_required("pos")
def delete_held(hid):
    db = get_db()
    db.execute("DELETE FROM held_sales WHERE id = ?", (hid,))
    db.commit()
    return jsonify({"ok": True})


@bp.get("/<int:sid>/receipt.pdf")
@login_required
def receipt_pdf(sid):
    """Render a thermal-printer-sized PDF receipt (58 mm or 80 mm)."""
    from flask import send_file
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    sale = query(
        "SELECT s.*, u.username AS cashier FROM sales s LEFT JOIN users u ON u.id=s.user_id "
        "WHERE s.id=?", (sid,), one=True)
    if not sale:
        return jsonify({"error": "not found"}), 404
    items = query("SELECT * FROM sale_items WHERE sale_id=?", (sid,))
    st = {r["key"]: r["value"] for r in query("SELECT key, value FROM settings")}
    width_mm = 58 if st.get("receipt_width") == "58" else 80
    cur = st.get("currency", "MAD")

    page_w = width_mm * mm
    line_h = 4.2 * mm
    height = (18 + len(items)) * line_h + 60 * mm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, height))
    x = 3 * mm
    y = height - 6 * mm

    def center(text, size=8, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawCentredString(page_w / 2, y, text)
        y -= line_h

    def row(left, right, size=7, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, str(left)[:26])
        c.drawRightString(page_w - x, y, str(right))
        y -= line_h

    def sep():
        nonlocal y
        c.setDash(1, 2)
        c.line(x, y, page_w - x, y)
        c.setDash()
        y -= line_h

    center(st.get("store_name", "KAKA Market"), 11, True)
    if st.get("store_address"):
        center(st["store_address"], 7)
    if st.get("store_phone"):
        center(f"Tel: {st['store_phone']}", 7)
    sep()
    row(f"Receipt: {sale['receipt_no']}", "")
    row(f"Date: {sale['created_at']}", "")
    row(f"Cashier: {sale['cashier'] or ''}", "")
    sep()
    for it in items:
        row(it["name"], f"{it['line_total']:.2f}", 7)
        row(f"  {it['quantity']:g} x {it['unit_price']:.2f}", "", 6)
    sep()
    row("Subtotal", f"{sale['subtotal']:.2f} {cur}", 8)
    if sale["discount"]:
        row("Discount", f"-{sale['discount']:.2f}", 8)
    row("Tax", f"{sale['tax']:.2f}", 8)
    row("TOTAL", f"{sale['total']:.2f} {cur}", 10, True)
    row("Paid", f"{sale['paid']:.2f}", 8)
    row("Change", f"{sale['change_due']:.2f}", 8)
    sep()
    center(st.get("receipt_footer", "Thank you!"), 8)
    c.showPage()
    c.save()
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     download_name=f"receipt_{sale['receipt_no']}.pdf")
