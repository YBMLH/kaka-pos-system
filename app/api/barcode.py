"""Barcode & QR generation, validation, and printable labels."""
import io

from flask import Blueprint, jsonify, request, send_file

from ..database import query
from ..utils.security import login_required

bp = Blueprint("barcode", __name__, url_prefix="/api/barcode")

SUPPORTED = {"ean13", "ean8", "upc", "code128", "code39", "qr"}


def _validate_ean13(code: str) -> bool:
    if len(code) != 13 or not code.isdigit():
        return False
    digits = [int(d) for d in code]
    check = (10 - (sum(digits[0:12:2]) + sum(digits[1:12:2]) * 3) % 10) % 10
    return check == digits[12]


def _validate_ean8(code: str) -> bool:
    if len(code) != 8 or not code.isdigit():
        return False
    digits = [int(d) for d in code]
    check = (10 - (sum(digits[0:7:2]) * 3 + sum(digits[1:7:2])) % 10) % 10
    return check == digits[7]


def _validate_upca(code: str) -> bool:
    if len(code) != 12 or not code.isdigit():
        return False
    digits = [int(d) for d in code]
    check = (10 - (sum(digits[0:11:2]) * 3 + sum(digits[1:11:2])) % 10) % 10
    return check == digits[11]


@bp.get("/validate")
@login_required
def validate():
    code = (request.args.get("code") or "").strip()
    symbology = (request.args.get("type") or "").lower()
    result = {"ean13": _validate_ean13, "ean8": _validate_ean8, "upc": _validate_upca}
    valid = result[symbology](code) if symbology in result else bool(code)
    return jsonify({"valid": valid, "code": code, "type": symbology})


@bp.get("/generate")
@login_required
def generate():
    """Return a PNG image for the given code/symbology.

    ``type`` one of: ean13, ean8, upc, code128, code39, qr.
    """
    code = (request.args.get("code") or "").strip()
    symbology = (request.args.get("type") or "code128").lower()
    if not code:
        return jsonify({"error": "code required"}), 400
    if symbology not in SUPPORTED:
        return jsonify({"error": "unsupported symbology"}), 400

    buf = io.BytesIO()
    try:
        if symbology == "qr":
            import qrcode
            img = qrcode.make(code)
            img.save(buf, format="PNG")
        else:
            import barcode as pybarcode
            from barcode.writer import ImageWriter
            cls_map = {
                "ean13": "ean13", "ean8": "ean8", "upc": "upca",
                "code128": "code128", "code39": "code39",
            }
            bc_cls = pybarcode.get_barcode_class(cls_map[symbology])
            bc = bc_cls(code, writer=ImageWriter())
            bc.write(buf)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"could not generate barcode: {exc}"}), 400
    buf.seek(0)
    return send_file(buf, mimetype="image/png",
                     download_name=f"{symbology}_{code}.png")


@bp.get("/label/<int:pid>")
@login_required
def product_label(pid):
    """Generate a printable price/barcode label PDF for a product."""
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    prod = query("SELECT * FROM products WHERE id = ?", (pid,), one=True)
    if not prod:
        return jsonify({"error": "not found"}), 404
    count = min(int(request.args.get("count", 1)), 40)
    currency = query("SELECT value FROM settings WHERE key='currency'", one=True)
    cur = currency["value"] if currency else "MAD"

    # Barcode image (Code128 works for any code).
    bc_buf = io.BytesIO()
    have_barcode = False
    if prod["barcode"]:
        try:
            import barcode as pybarcode
            from barcode.writer import ImageWriter
            bc = pybarcode.get_barcode_class("code128")(prod["barcode"], writer=ImageWriter())
            bc.write(bc_buf)
            bc_buf.seek(0)
            have_barcode = True
        except Exception:  # noqa: BLE001
            have_barcode = False

    from reportlab.lib.utils import ImageReader
    label_w, label_h = 50 * mm, 30 * mm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(label_w, label_h))
    for _ in range(count):
        c.setFont("Helvetica-Bold", 7)
        name = (prod["name_en"] or prod["name_ar"] or "")[:34]
        c.drawCentredString(label_w / 2, label_h - 5 * mm, name)
        if have_barcode:
            bc_buf.seek(0)
            c.drawImage(ImageReader(bc_buf), 5 * mm, 8 * mm, width=40 * mm, height=12 * mm,
                        preserveAspectRatio=True, mask="auto")
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(label_w / 2, 3 * mm, f"{prod['selling_price']:,.2f} {cur}")
        c.showPage()
    c.save()
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     download_name=f"label_{pid}.pdf")
