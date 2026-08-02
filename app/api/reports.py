"""Reports API: sales, inventory, supplier, customer, financial, employee.

Every report can be returned as JSON (for on-screen tables) or exported as
Excel / CSV / PDF via the ``format`` query parameter.
"""
import csv
import io

from flask import Blueprint, jsonify, request, send_file

from ..database import query
from ..utils.security import login_required

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _range_filter(alias="s", column="created_at"):
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    clauses, params = [], []
    if date_from:
        clauses.append(f"date({alias}.{column}) >= ?")
        params.append(date_from)
    if date_to:
        clauses.append(f"date({alias}.{column}) <= ?")
        params.append(date_to)
    return (" AND " + " AND ".join(clauses)) if clauses else "", params


def _export(rows, headers, keys, name):
    fmt = request.args.get("format", "json")
    if fmt == "json" or not rows:
        if fmt in ("excel", "csv", "pdf") and not rows:
            pass  # fall through to produce an empty file
        else:
            return None
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(headers)
        for r in rows:
            w.writerow([r.get(k, "") for k in keys])
        data = io.BytesIO(buf.getvalue().encode("utf-8-sig"))
        return send_file(data, as_attachment=True, download_name=f"{name}.csv",
                         mimetype="text/csv")
    if fmt == "excel":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = name[:30]
        ws.append(headers)
        for r in rows:
            ws.append([r.get(k, "") for k in keys])
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return send_file(out, as_attachment=True, download_name=f"{name}.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if fmt == "pdf":
        return _pdf_table(name.replace("_", " ").title(), headers, keys, rows, name)
    return None


def _pdf_table(title, headers, keys, rows, name):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    store = query("SELECT value FROM settings WHERE key='store_name'", one=True)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title=title)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(store["value"] if store else "KAKA Market", styles["Title"]),
        Paragraph(title, styles["Heading2"]),
        Spacer(1, 12),
    ]
    data = [headers] + [[str(r.get(k, "")) for k in keys] for r in rows]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6feb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6fc")]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{name}.pdf",
                     mimetype="application/pdf")


# --------------------------------------------------------------------------- #
# Sales reports
# --------------------------------------------------------------------------- #
@bp.get("/sales")
@login_required
def sales_report():
    group = request.args.get("group", "day")
    fmt_map = {
        "day": "date(s.created_at)", "week": "strftime('%Y-W%W', s.created_at)",
        "month": "strftime('%Y-%m', s.created_at)", "quarter": "strftime('%Y', s.created_at)",
        "year": "strftime('%Y', s.created_at)",
    }
    bucket = fmt_map.get(group, fmt_map["day"])
    rf, params = _range_filter()
    rows = query(
        f"SELECT {bucket} AS period, COUNT(*) AS orders, "
        f"COALESCE(SUM(s.total),0) AS revenue, COALESCE(SUM(s.profit),0) AS profit, "
        f"COALESCE(SUM(s.tax),0) AS tax, COALESCE(SUM(s.discount),0) AS discount "
        f"FROM sales s WHERE s.status='completed'{rf} GROUP BY period ORDER BY period DESC",
        params)
    data = [dict(r) for r in rows]
    exported = _export(data, ["Period", "Orders", "Revenue", "Profit", "Tax", "Discount"],
                       ["period", "orders", "revenue", "profit", "tax", "discount"], "sales_report")
    if exported is not None:
        return exported
    totals = {
        "orders": sum(r["orders"] for r in data),
        "revenue": round(sum(r["revenue"] for r in data), 2),
        "profit": round(sum(r["profit"] for r in data), 2),
    }
    return jsonify({"rows": data, "totals": totals})


# --------------------------------------------------------------------------- #
# Inventory reports
# --------------------------------------------------------------------------- #
@bp.get("/inventory")
@login_required
def inventory_report():
    kind = request.args.get("kind", "stock")
    if kind == "low":
        where = "is_archived=0 AND quantity <= min_stock AND min_stock > 0"
    elif kind == "out":
        where = "is_archived=0 AND quantity <= 0"
    elif kind == "expiry":
        where = ("is_archived=0 AND expiry_date IS NOT NULL AND expiry_date != '' "
                 "AND date(expiry_date) <= date('now','localtime','+60 day')")
    else:
        where = "is_archived=0"
    rows = query(
        f"SELECT p.name_en AS name, p.barcode, p.quantity, p.min_stock, p.unit, "
        f"p.purchase_price, p.selling_price, p.expiry_date, "
        f"ROUND(p.quantity*p.purchase_price,2) AS stock_value "
        f"FROM products p WHERE {where} ORDER BY p.name_en LIMIT 5000")
    data = [dict(r) for r in rows]
    exported = _export(
        data, ["Name", "Barcode", "Qty", "Min", "Unit", "Cost", "Price", "Expiry", "Stock Value"],
        ["name", "barcode", "quantity", "min_stock", "unit", "purchase_price",
         "selling_price", "expiry_date", "stock_value"], "inventory_report")
    if exported is not None:
        return exported
    return jsonify({"rows": data,
                    "total_value": round(sum(r["stock_value"] or 0 for r in data), 2)})


# --------------------------------------------------------------------------- #
# Supplier / customer / financial / employee reports
# --------------------------------------------------------------------------- #
@bp.get("/suppliers")
@login_required
def supplier_report():
    rows = query(
        "SELECT s.company_name AS name, s.phone1, s.balance, "
        "(SELECT COUNT(*) FROM purchases p WHERE p.supplier_id=s.id) AS orders, "
        "(SELECT COALESCE(SUM(total),0) FROM purchases p WHERE p.supplier_id=s.id) AS purchased "
        "FROM suppliers s WHERE s.is_active=1 ORDER BY s.balance DESC")
    data = [dict(r) for r in rows]
    exported = _export(data, ["Supplier", "Phone", "Balance", "Orders", "Total Purchased"],
                       ["name", "phone1", "balance", "orders", "purchased"], "supplier_report")
    if exported is not None:
        return exported
    return jsonify({"rows": data})


@bp.get("/customers")
@login_required
def customer_report():
    rows = query(
        "SELECT c.name, c.phone, c.loyalty_pts, c.credit, "
        "(SELECT COUNT(*) FROM sales s WHERE s.customer_id=c.id AND s.status='completed') AS orders, "
        "(SELECT COALESCE(SUM(total),0) FROM sales s WHERE s.customer_id=c.id AND s.status='completed') AS spent "
        "FROM customers c WHERE c.is_active=1 ORDER BY spent DESC")
    data = [dict(r) for r in rows]
    exported = _export(data, ["Name", "Phone", "Loyalty", "Credit", "Orders", "Total Spent"],
                       ["name", "phone", "loyalty_pts", "credit", "orders", "spent"], "customer_report")
    if exported is not None:
        return exported
    return jsonify({"rows": data})


@bp.get("/financial")
@login_required
def financial_report():
    rf, params = _range_filter()
    sales = query(
        f"SELECT COALESCE(SUM(total),0) AS revenue, COALESCE(SUM(cost_total),0) AS cost, "
        f"COALESCE(SUM(profit),0) AS gross_profit, COALESCE(SUM(tax),0) AS tax "
        f"FROM sales s WHERE s.status='completed'{rf}", params, one=True)
    erf, eparams = _range_filter(alias="e", column="spent_on")
    expenses = query(
        f"SELECT COALESCE(SUM(amount),0) AS total FROM expenses e WHERE 1=1{erf}", eparams, one=True)
    by_cat = query(
        f"SELECT category, SUM(amount) AS total FROM expenses e WHERE 1=1{erf} "
        f"GROUP BY category ORDER BY total DESC", eparams)
    gross = sales["gross_profit"]
    net = gross - expenses["total"]
    report = {
        "revenue": round(sales["revenue"], 2),
        "cost_of_goods": round(sales["cost"], 2),
        "gross_profit": round(gross, 2),
        "tax_collected": round(sales["tax"], 2),
        "expenses": round(expenses["total"], 2),
        "net_profit": round(net, 2),
        "expenses_by_category": [dict(r) for r in by_cat],
    }
    if request.args.get("format") in ("excel", "csv", "pdf"):
        rows = [
            {"metric": "Revenue", "amount": report["revenue"]},
            {"metric": "Cost of Goods", "amount": report["cost_of_goods"]},
            {"metric": "Gross Profit", "amount": report["gross_profit"]},
            {"metric": "Tax Collected", "amount": report["tax_collected"]},
            {"metric": "Expenses", "amount": report["expenses"]},
            {"metric": "Net Profit", "amount": report["net_profit"]},
        ]
        return _export(rows, ["Metric", "Amount"], ["metric", "amount"], "financial_report")
    return jsonify(report)


@bp.get("/employees")
@login_required
def employee_report():
    rf, params = _range_filter()
    rows = query(
        f"SELECT u.username, u.full_name, COUNT(s.id) AS transactions, "
        f"COALESCE(SUM(s.total),0) AS revenue, COALESCE(SUM(s.profit),0) AS profit "
        f"FROM users u LEFT JOIN sales s ON s.user_id=u.id AND s.status='completed'{rf} "
        f"GROUP BY u.id ORDER BY revenue DESC", params)
    data = [dict(r) for r in rows]
    exported = _export(data, ["Username", "Name", "Transactions", "Revenue", "Profit"],
                       ["username", "full_name", "transactions", "revenue", "profit"],
                       "employee_report")
    if exported is not None:
        return exported
    return jsonify({"rows": data})
