"""Zakat calculator module.

Zakat is due on zakatable wealth held for a lunar year (hawl) above the nisab
threshold, at 2.5%. This module computes the amount from live business figures
(cash, bank, inventory value, receivables) minus short-term debts, and lets the
user override any input. It shows the full calculation for transparency.
"""
import io

from flask import Blueprint, jsonify, request, send_file

from ..database import query
from ..utils.security import login_required

bp = Blueprint("zakat", __name__, url_prefix="/api/zakat")


def _default_inputs() -> dict:
    inv = query(
        "SELECT COALESCE(SUM(quantity*purchase_price),0) AS v FROM products WHERE is_archived=0",
        one=True)["v"]
    receivables = query(
        "SELECT COALESCE(SUM(credit),0) AS c FROM customers WHERE is_active=1", one=True)["c"]
    # Cash on hand estimate: sum of open registers' expected cash.
    cash = query(
        "SELECT COALESCE(SUM(opening_cash),0) AS c FROM registers WHERE status='open'",
        one=True)["c"]
    debts = query(
        "SELECT COALESCE(SUM(balance),0) AS d FROM suppliers WHERE balance>0", one=True)["d"]
    return {
        "cash_on_hand": round(cash, 2),
        "bank_balance": 0.0,
        "inventory_value": round(inv, 2),
        "receivables": round(receivables, 2),
        "debts": round(debts, 2),
    }


def _rate() -> float:
    row = query("SELECT value FROM settings WHERE key='zakat_rate'", one=True)
    try:
        return float(row["value"]) if row else 2.5
    except (ValueError, TypeError):
        return 2.5


def _calculate(inputs: dict, rate: float) -> dict:
    zakatable = (
        float(inputs.get("cash_on_hand", 0))
        + float(inputs.get("bank_balance", 0))
        + float(inputs.get("inventory_value", 0))
        + float(inputs.get("receivables", 0))
        - float(inputs.get("debts", 0))
    )
    zakatable = max(zakatable, 0)
    due = round(zakatable * rate / 100, 2)
    return {
        "inputs": inputs,
        "rate": rate,
        "net_zakatable": round(zakatable, 2),
        "zakat_due": due,
        "monthly_estimate": round(due / 12, 2),
        "quarterly_estimate": round(due / 4, 2),
        "yearly_estimate": due,
    }


@bp.get("/defaults")
@login_required
def defaults():
    inputs = _default_inputs()
    return jsonify(_calculate(inputs, _rate()))


@bp.post("/calculate")
@login_required
def calculate():
    data = request.get_json(silent=True) or {}
    base = _default_inputs()
    inputs = {k: float(data.get(k, base[k])) for k in base}
    rate = float(data.get("rate", _rate()))
    return jsonify(_calculate(inputs, rate))


@bp.post("/report")
@login_required
def report():
    """Generate a printable PDF zakat report."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    data = request.get_json(silent=True) or {}
    base = _default_inputs()
    inputs = {k: float(data.get(k, base[k])) for k in base}
    result = _calculate(inputs, float(data.get("rate", _rate())))

    store = query("SELECT value FROM settings WHERE key='store_name'", one=True)
    currency = query("SELECT value FROM settings WHERE key='currency'", one=True)
    store_name = store["value"] if store else "KAKA Market"
    cur = currency["value"] if currency else "MAD"

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 25 * mm
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, y, "Zakat Report")
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y, store_name)
    y -= 15 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "Zakatable Assets")
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    for label, key in [("Cash on hand", "cash_on_hand"), ("Bank balance", "bank_balance"),
                       ("Inventory value", "inventory_value"), ("Receivables", "receivables")]:
        c.drawString(30 * mm, y, label)
        c.drawRightString(170 * mm, y, f"{inputs[key]:,.2f} {cur}")
        y -= 7 * mm
    y -= 3 * mm
    c.drawString(30 * mm, y, "Less: Debts")
    c.drawRightString(170 * mm, y, f"-{inputs['debts']:,.2f} {cur}")
    y -= 10 * mm
    c.line(25 * mm, y, 170 * mm, y)
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, "Net Zakatable Wealth")
    c.drawRightString(170 * mm, y, f"{result['net_zakatable']:,.2f} {cur}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"Zakat Rate")
    c.drawRightString(170 * mm, y, f"{result['rate']}%")
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30 * mm, y, "Zakat Due")
    c.drawRightString(170 * mm, y, f"{result['zakat_due']:,.2f} {cur}")
    y -= 20 * mm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(25 * mm, y, "Calculation: (Cash + Bank + Inventory + Receivables - Debts) x Rate")
    c.showPage()
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="zakat_report.pdf",
                     mimetype="application/pdf")
