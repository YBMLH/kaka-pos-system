"""Dashboard & business-health analytics API.

All figures come from completed sales, expenses and current inventory. Period
boundaries use SQLite date functions against ``created_at`` (local time).
"""
from flask import Blueprint, jsonify, request

from ..database import query
from ..utils.security import login_required

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

# SQLite date predicates for each named period (relative to now, local time).
PERIODS = {
    "today": "date(s.created_at) = date('now','localtime')",
    "yesterday": "date(s.created_at) = date('now','localtime','-1 day')",
    "week": "date(s.created_at) >= date('now','localtime','weekday 0','-6 days')",
    "month": "strftime('%Y-%m', s.created_at) = strftime('%Y-%m','now','localtime')",
    "quarter": ("strftime('%Y', s.created_at) = strftime('%Y','now','localtime') AND "
                "((strftime('%m', s.created_at)+2)/3) = ((strftime('%m','now','localtime')+2)/3)"),
    "half": ("strftime('%Y', s.created_at) = strftime('%Y','now','localtime') AND "
             "((strftime('%m', s.created_at)+5)/6) = ((strftime('%m','now','localtime')+5)/6)"),
    "year": "strftime('%Y', s.created_at) = strftime('%Y','now','localtime')",
}

EXPENSE_PERIODS = {
    "today": "spent_on = date('now','localtime')",
    "week": "spent_on >= date('now','localtime','weekday 0','-6 days')",
    "month": "strftime('%Y-%m', spent_on) = strftime('%Y-%m','now','localtime')",
    "quarter": ("strftime('%Y', spent_on) = strftime('%Y','now','localtime') AND "
                "((strftime('%m', spent_on)+2)/3) = ((strftime('%m','now','localtime')+2)/3)"),
    "year": "strftime('%Y', spent_on) = strftime('%Y','now','localtime')",
}


def _sales_metrics(where: str) -> dict:
    row = query(
        f"SELECT COUNT(*) AS orders, COALESCE(SUM(total),0) AS revenue, "
        f"COALESCE(SUM(cost_total),0) AS cost, COALESCE(SUM(profit),0) AS gross_profit, "
        f"COALESCE(SUM(tax),0) AS tax, COALESCE(SUM(discount),0) AS discount "
        f"FROM sales s WHERE s.status='completed' AND {where}", one=True)
    return {
        "orders": row["orders"],
        "revenue": round(row["revenue"], 2),
        "cost": round(row["cost"], 2),
        "gross_profit": round(row["gross_profit"], 2),
        "tax": round(row["tax"], 2),
        "discount": round(row["discount"], 2),
    }


def _expense_total(where: str) -> float:
    row = query(f"SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE {where}", one=True)
    return round(row["t"], 2)


@bp.get("/summary")
@login_required
def summary():
    """Headline metrics for every period plus inventory value and net profit."""
    out = {}
    for name, where in PERIODS.items():
        m = _sales_metrics(where)
        exp = _expense_total(EXPENSE_PERIODS.get(name, "0")) if name in EXPENSE_PERIODS else 0
        m["expenses"] = exp
        m["net_profit"] = round(m["gross_profit"] - exp, 2)
        out[name] = m

    inv = query(
        "SELECT COALESCE(SUM(quantity*purchase_price),0) AS cost_value, "
        "COALESCE(SUM(quantity*selling_price),0) AS retail_value "
        "FROM products WHERE is_archived=0", one=True)
    out["inventory"] = {
        "cost_value": round(inv["cost_value"], 2),
        "retail_value": round(inv["retail_value"], 2),
        "potential_profit": round(inv["retail_value"] - inv["cost_value"], 2),
    }
    # Cash flow: today's cash in (sales) vs out (expenses).
    cash_in = query(
        "SELECT COALESCE(SUM(total),0) AS t FROM sales s WHERE status='completed' AND "
        "payment_method IN ('cash','mixed') AND " + PERIODS["today"], one=True)["t"]
    out["cash_flow_today"] = round(cash_in - out["today"]["expenses"], 2)
    return jsonify(out)


def _compare(current_where, previous_where, expense_current, expense_previous):
    cur = _sales_metrics(current_where)
    prev = _sales_metrics(previous_where)
    cur_exp = _expense_total(expense_current)
    prev_exp = _expense_total(expense_previous)

    def growth(a, b):
        if b == 0:
            return 100.0 if a > 0 else 0.0
        return round((a - b) / b * 100, 2)

    return {
        "current": {**cur, "expenses": cur_exp,
                    "net_profit": round(cur["gross_profit"] - cur_exp, 2)},
        "previous": {**prev, "expenses": prev_exp,
                     "net_profit": round(prev["gross_profit"] - prev_exp, 2)},
        "revenue_diff": round(cur["revenue"] - prev["revenue"], 2),
        "profit_diff": round(cur["gross_profit"] - prev["gross_profit"], 2),
        "expense_diff": round(cur_exp - prev_exp, 2),
        "revenue_growth": growth(cur["revenue"], prev["revenue"]),
        "profit_growth": growth(cur["gross_profit"], prev["gross_profit"]),
    }


@bp.get("/comparisons")
@login_required
def comparisons():
    C = {
        "day": _compare(
            PERIODS["today"], PERIODS["yesterday"],
            EXPENSE_PERIODS["today"], "spent_on = date('now','localtime','-1 day')"),
        "week": _compare(
            PERIODS["week"],
            "date(s.created_at) >= date('now','localtime','weekday 0','-13 days') AND "
            "date(s.created_at) < date('now','localtime','weekday 0','-6 days')",
            EXPENSE_PERIODS["week"],
            "spent_on >= date('now','localtime','weekday 0','-13 days') AND "
            "spent_on < date('now','localtime','weekday 0','-6 days')"),
        "month": _compare(
            PERIODS["month"],
            "strftime('%Y-%m', s.created_at) = strftime('%Y-%m','now','localtime','-1 month')",
            EXPENSE_PERIODS["month"],
            "strftime('%Y-%m', spent_on) = strftime('%Y-%m','now','localtime','-1 month')"),
        "year": _compare(
            PERIODS["year"],
            "strftime('%Y', s.created_at) = strftime('%Y','now','localtime','-1 year')",
            EXPENSE_PERIODS["year"],
            "strftime('%Y', spent_on) = strftime('%Y','now','localtime','-1 year')"),
    }
    return jsonify(C)


@bp.get("/chart")
@login_required
def chart():
    """Time series for the revenue chart. ``range`` = 7d | 30d | 12m."""
    rng = request.args.get("range", "30d")
    if rng == "7d":
        rows = query(
            "SELECT date(created_at) AS label, SUM(total) AS revenue, SUM(profit) AS profit "
            "FROM sales WHERE status='completed' AND "
            "date(created_at) >= date('now','localtime','-6 days') "
            "GROUP BY label ORDER BY label")
    elif rng == "12m":
        rows = query(
            "SELECT strftime('%Y-%m', created_at) AS label, SUM(total) AS revenue, "
            "SUM(profit) AS profit FROM sales WHERE status='completed' AND "
            "created_at >= date('now','localtime','-11 months','start of month') "
            "GROUP BY label ORDER BY label")
    else:  # 30d
        rows = query(
            "SELECT date(created_at) AS label, SUM(total) AS revenue, SUM(profit) AS profit "
            "FROM sales WHERE status='completed' AND "
            "date(created_at) >= date('now','localtime','-29 days') "
            "GROUP BY label ORDER BY label")
    return jsonify({"series": [
        {"label": r["label"], "revenue": round(r["revenue"] or 0, 2),
         "profit": round(r["profit"] or 0, 2)} for r in rows]})


@bp.get("/top")
@login_required
def top_lists():
    products = query(
        "SELECT si.name, SUM(si.quantity) AS qty, SUM(si.line_total) AS revenue "
        "FROM sale_items si JOIN sales s ON s.id=si.sale_id "
        "WHERE s.status='completed' AND date(s.created_at) >= date('now','localtime','-30 days') "
        "GROUP BY si.product_id ORDER BY qty DESC LIMIT 10")
    categories = query(
        "SELECT COALESCE(c.name,'Uncategorized') AS name, SUM(si.line_total) AS revenue "
        "FROM sale_items si JOIN sales s ON s.id=si.sale_id "
        "LEFT JOIN products p ON p.id=si.product_id LEFT JOIN categories c ON c.id=p.category_id "
        "WHERE s.status='completed' AND date(s.created_at) >= date('now','localtime','-30 days') "
        "GROUP BY c.name ORDER BY revenue DESC LIMIT 10")
    return jsonify({
        "top_products": [dict(r) for r in products],
        "top_categories": [dict(r) for r in categories],
    })


@bp.get("/health")
@login_required
def health():
    """Business-health traffic lights based on simple, transparent thresholds."""
    month = _sales_metrics(PERIODS["month"])
    month_exp = _expense_total(EXPENSE_PERIODS["month"])
    net = month["gross_profit"] - month_exp

    prev_where = "strftime('%Y-%m', s.created_at) = strftime('%Y-%m','now','localtime','-1 month')"
    prev = _sales_metrics(prev_where)
    revenue_trend = month["revenue"] - prev["revenue"]

    inv = query(
        "SELECT COALESCE(SUM(quantity*purchase_price),0) AS v FROM products WHERE is_archived=0",
        one=True)["v"]
    low_stock = query(
        "SELECT COUNT(*) AS c FROM products WHERE is_archived=0 AND quantity<=min_stock "
        "AND min_stock>0", one=True)["c"]
    supplier_debt = query(
        "SELECT COALESCE(SUM(balance),0) AS d FROM suppliers WHERE balance>0", one=True)["d"]

    def light(value, good, warn):
        if value >= good:
            return "green"
        if value >= warn:
            return "orange"
        return "red"

    margin = (net / month["revenue"] * 100) if month["revenue"] else 0
    indicators = {
        "profitability": {"value": round(net, 2), "status": light(net, 1, 0),
                          "label": "Net profit this month"},
        "margin": {"value": round(margin, 1), "status": light(margin, 15, 5),
                   "label": "Net margin %"},
        "revenue_trend": {"value": round(revenue_trend, 2),
                          "status": light(revenue_trend, 0.01, -0.01),
                          "label": "Revenue vs last month"},
        "stock_health": {"value": low_stock,
                         "status": "green" if low_stock == 0 else ("orange" if low_stock < 15 else "red"),
                         "label": "Products at/below minimum"},
    }
    overall_red = any(i["status"] == "red" for i in indicators.values())
    overall_orange = any(i["status"] == "orange" for i in indicators.values())
    overall = "red" if overall_red else ("orange" if overall_orange else "green")
    return jsonify({
        "indicators": indicators,
        "overall": overall,
        "net_worth_estimate": round(inv + net - supplier_debt, 2),
        "inventory_value": round(inv, 2),
        "supplier_debt": round(supplier_debt, 2),
    })
