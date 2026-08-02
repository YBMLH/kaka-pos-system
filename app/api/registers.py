"""Cash register API: open / close with cash counting and difference detection."""
from flask import Blueprint, g, jsonify, request

from ..database import get_db, query
from ..utils.audit import log_action
from ..utils.security import permission_required

bp = Blueprint("registers", __name__, url_prefix="/api/registers")


@bp.get("/current")
@permission_required("register")
def current():
    row = query(
        "SELECT * FROM registers WHERE status='open' AND user_id=? ORDER BY id DESC LIMIT 1",
        (g.user["id"],), one=True)
    if not row:
        return jsonify({"register": None})
    # Cash sales recorded during this open session.
    cash = query(
        "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE register_id=? "
        "AND status='completed' AND payment_method IN ('cash','mixed')",
        (row["id"],), one=True)["t"]
    d = dict(row)
    d["cash_sales"] = round(cash, 2)
    d["expected_cash"] = round((row["opening_cash"] or 0) + cash, 2)
    return jsonify({"register": d})


@bp.post("/open")
@permission_required("register")
def open_register():
    existing = query(
        "SELECT id FROM registers WHERE status='open' AND user_id=?", (g.user["id"],), one=True)
    if existing:
        return jsonify({"error": "a register is already open", "id": existing["id"]}), 409
    data = request.get_json(silent=True) or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO registers (user_id, opening_cash, note) VALUES (?,?,?)",
        (g.user["id"], float(data.get("opening_cash") or 0), data.get("note", "")))
    db.commit()
    log_action("open_register", "register", cur.lastrowid)
    return jsonify({"id": cur.lastrowid}), 201


@bp.post("/close")
@permission_required("register")
def close_register():
    data = request.get_json(silent=True) or {}
    db = get_db()
    reg = db.execute(
        "SELECT * FROM registers WHERE status='open' AND user_id=? ORDER BY id DESC LIMIT 1",
        (g.user["id"],)).fetchone()
    if not reg:
        return jsonify({"error": "no open register"}), 404
    cash = db.execute(
        "SELECT COALESCE(SUM(total),0) AS t FROM sales WHERE register_id=? "
        "AND status='completed' AND payment_method IN ('cash','mixed')",
        (reg["id"],)).fetchone()["t"]
    expected = (reg["opening_cash"] or 0) + cash
    counted = float(data.get("counted_cash") or 0)
    difference = round(counted - expected, 2)
    db.execute(
        "UPDATE registers SET status='closed', closing_cash=?, counted_cash=?, "
        "expected_cash=?, difference=?, closed_at=datetime('now','localtime'), note=? WHERE id=?",
        (counted, counted, round(expected, 2), difference, data.get("note", ""), reg["id"]))
    db.commit()
    log_action("close_register", "register", reg["id"], f"difference={difference}")
    return jsonify({"ok": True, "expected_cash": round(expected, 2),
                    "counted_cash": counted, "difference": difference})


@bp.get("/history")
@permission_required("register")
def history():
    rows = query(
        "SELECT r.*, u.username FROM registers r LEFT JOIN users u ON u.id=r.user_id "
        "ORDER BY r.id DESC LIMIT 100")
    return jsonify({"registers": [dict(r) for r in rows]})
