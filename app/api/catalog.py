"""Categories & brands API — supporting reference data for products."""
from flask import Blueprint, jsonify, request

from ..database import execute, query
from ..utils.audit import log_action
from ..utils.security import login_required, permission_required

bp = Blueprint("catalog", __name__, url_prefix="/api/catalog")


@bp.get("/categories")
@login_required
def list_categories():
    rows = query(
        "SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id=c.id) AS product_count "
        "FROM categories c ORDER BY c.name")
    return jsonify({"categories": [dict(r) for r in rows]})


@bp.post("/categories")
@permission_required("products.edit")
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    dup = query("SELECT id FROM categories WHERE name = ?", (name,), one=True)
    if dup:
        return jsonify({"id": dup["id"], "existing": True})
    cid = execute(
        "INSERT INTO categories (name, name_ar, name_fr) VALUES (?,?,?)",
        (name, data.get("name_ar", ""), data.get("name_fr", "")),
    )
    log_action("create_category", "category", cid, name)
    return jsonify({"id": cid}), 201


@bp.put("/categories/<int:cid>")
@permission_required("products.edit")
def update_category(cid):
    data = request.get_json(silent=True) or {}
    execute(
        "UPDATE categories SET name=?, name_ar=?, name_fr=? WHERE id=?",
        (data.get("name", ""), data.get("name_ar", ""), data.get("name_fr", ""), cid),
    )
    return jsonify({"ok": True})


@bp.delete("/categories/<int:cid>")
@permission_required("products.edit")
def delete_category(cid):
    execute("UPDATE products SET category_id = NULL WHERE category_id = ?", (cid,))
    execute("DELETE FROM categories WHERE id = ?", (cid,))
    return jsonify({"ok": True})


@bp.get("/brands")
@login_required
def list_brands():
    rows = query("SELECT * FROM brands ORDER BY name")
    return jsonify({"brands": [dict(r) for r in rows]})


@bp.post("/brands")
@permission_required("products.edit")
def create_brand():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    dup = query("SELECT id FROM brands WHERE name = ?", (name,), one=True)
    if dup:
        return jsonify({"id": dup["id"], "existing": True})
    bid = execute("INSERT INTO brands (name) VALUES (?)", (name,))
    return jsonify({"id": bid}), 201


@bp.delete("/brands/<int:bid>")
@permission_required("products.edit")
def delete_brand(bid):
    execute("UPDATE products SET brand_id = NULL WHERE brand_id = ?", (bid,))
    execute("DELETE FROM brands WHERE id = ?", (bid,))
    return jsonify({"ok": True})
