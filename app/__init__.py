"""Application factory for KAKA POS."""
import json

from flask import Flask, g, render_template, session

from .config import Config
from .database import close_db, get_db
from .utils.security import role_permissions


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)

    app.teardown_appcontext(close_db)

    @app.before_request
    def load_logged_in_user():
        """Attach the current user (with resolved permissions) to ``g``."""
        g.user = None
        user_id = session.get("user_id")
        if user_id is None:
            return
        row = get_db().execute(
            "SELECT u.*, r.name AS role_name, r.label AS role_label, "
            "r.permissions AS role_permissions "
            "FROM users u JOIN roles r ON r.id = u.role_id "
            "WHERE u.id = ? AND u.is_active = 1",
            (user_id,),
        ).fetchone()
        if row is None:
            session.clear()
            return
        user = dict(row)
        user["permissions"] = role_permissions(user.pop("role_permissions"))
        g.user = user

    # ---- Blueprints -------------------------------------------------------
    from .auth import bp as auth_bp
    from .api.products import bp as products_bp
    from .api.sales import bp as sales_bp
    from .api.inventory import bp as inventory_bp
    from .api.suppliers import bp as suppliers_bp
    from .api.customers import bp as customers_bp
    from .api.purchases import bp as purchases_bp
    from .api.expenses import bp as expenses_bp
    from .api.reports import bp as reports_bp
    from .api.dashboard import bp as dashboard_bp
    from .api.zakat import bp as zakat_bp
    from .api.backup import bp as backup_bp
    from .api.settings import bp as settings_bp
    from .api.users import bp as users_bp
    from .api.registers import bp as registers_bp
    from .api.barcode import bp as barcode_bp
    from .api.catalog import bp as catalog_bp

    for bp in (
        auth_bp, products_bp, sales_bp, inventory_bp, suppliers_bp,
        customers_bp, purchases_bp, expenses_bp, reports_bp, dashboard_bp,
        zakat_bp, backup_bp, settings_bp, users_bp, registers_bp,
        barcode_bp, catalog_bp,
    ):
        app.register_blueprint(bp)

    # ---- Frontend shell ---------------------------------------------------
    @app.route("/")
    def index():
        if not session.get("user_id"):
            return render_template("login.html")
        return render_template("app.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.context_processor
    def inject_settings():
        rows = get_db().execute("SELECT key, value FROM settings").fetchall()
        return {"settings": {r["key"]: r["value"] for r in rows}}

    @app.template_filter("tojson_safe")
    def tojson_safe(value):
        return json.dumps(value, ensure_ascii=False)

    return app
