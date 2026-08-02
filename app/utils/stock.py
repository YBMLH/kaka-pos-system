"""Shared inventory helpers — the single place stock levels are changed.

Every stock change goes through :func:`adjust_stock` so the
``inventory_movements`` ledger always mirrors ``products.quantity``.
"""
from flask import session

from ..database import get_db


def adjust_stock(db, product_id, change_qty, reason, ref_type="", ref_id=None, note=""):
    """Apply a stock delta and append a movement row. Returns new balance.

    Uses the provided connection ``db`` so callers can wrap several changes in
    one transaction (e.g. all line items of a sale) and commit once.
    """
    row = db.execute("SELECT quantity FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        return None
    new_balance = (row["quantity"] or 0) + change_qty
    db.execute(
        "UPDATE products SET quantity = ?, updated_at = datetime('now','localtime') WHERE id = ?",
        (new_balance, product_id),
    )
    db.execute(
        "INSERT INTO inventory_movements "
        "(product_id, change_qty, balance, reason, ref_type, ref_id, note, user_id) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (product_id, change_qty, new_balance, reason, ref_type, ref_id, note,
         session.get("user_id")),
    )
    return new_balance


def stock_level(product_id) -> float:
    row = get_db().execute("SELECT quantity FROM products WHERE id = ?", (product_id,)).fetchone()
    return (row["quantity"] if row else 0) or 0
