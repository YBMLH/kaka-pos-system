# KAKA POS — Offline Supermarket & Business Management System

A complete, production-ready **100% offline** Point of Sale and business
management system for supermarkets, grocery & mini markets, wholesale stores,
phone/electronics shops, clothing and general retail.

Built with **Python + Flask + SQLite** on the backend and **vanilla
HTML/CSS/JavaScript** on the frontend. No internet, no cloud, no external APIs —
all data stays on the local machine.

---

## Highlights

- **Offline-first** — runs entirely on one computer; the database is a single
  SQLite file.
- **Multi-language** — English, French and Arabic with full **RTL** support.
- **Light & Dark themes** — per-user preference, remembered across sessions.
- **Fast search** — instant barcode lookup plus accent-insensitive,
  Arabic-normalized, typo-tolerant product search (`coca`, `Coca-Cola`,
  `cocacola`, `كوكا` all match).
- **Role-based access** — Administrator, Manager, Cashier, Inventory Employee,
  each with a tailored permission set.
- **Optimized for scale** — WAL journaling and targeted indexes for
  50,000+ products and 100,000+ sales.

## Feature Modules

| Area | What it does |
|------|--------------|
| **Dashboard** | Revenue/profit/expense/net figures for today, week, month, quarter, half-year and year; period comparisons with growth %; revenue & profit charts; top products/categories; business-health traffic lights; net-worth & zakat estimate. |
| **Point of Sale** | Barcode scanning, instant search, cart with quantity/price/discount editing (permission-gated), cash/card/transfer/credit payments, change calculation, hold & resume, thermal receipt printing. |
| **Products** | Full CRUD, archive/restore/duplicate, per-product movement history, category & brand management, barcode/label printing, **Excel import & export**. |
| **Barcodes** | EAN-13/EAN-8/UPC/Code128/Code39/QR generation, checksum validation, printable price labels. |
| **Inventory** | Real-time stock, valuation, adjustments (damage/loss/expired/transfer), movement ledger, low-stock / out-of-stock / expiry alerts, physical count sessions. |
| **Suppliers** | CRUD, categories, balances/debts, payments, statements, purchase history. |
| **Purchases** | Draft/ordered orders, full & partial receiving, cost sync, **automatic reordering** (draft POs grouped by supplier when stock hits minimum). |
| **Customers** | CRUD, purchase history, loyalty points, store credit & settlement. |
| **Cash Register** | Open/close sessions, opening/closing cash, counting, difference detection, history. |
| **Expenses** | Categorized expense tracking with monthly reports. |
| **Reports** | Sales, inventory, supplier, customer, financial and employee reports, exportable to **PDF / Excel / CSV**. |
| **Zakat** | Dedicated 2.5% calculator on net zakatable wealth with printable PDF report and monthly/quarterly/yearly estimates. |
| **Users & Security** | User management, PBKDF2 password hashing, full audit/activity log, permission enforcement. |
| **Backup** | Automatic daily/weekly + manual snapshots, checksum verification, download, restore. |
| **Settings** | Store name/logo/address/phone, currency, tax rate, receipt width (58/80 mm), footer. |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) load sample data for a ready-to-explore install
python seed.py

# 3. Run
python run.py
```

Open <http://127.0.0.1:5000> and sign in with the default administrator:

```
username: admin
password: admin123
```

> Change the admin password immediately from the user menu → **Change Password**.

If you ran `seed.py`, a demo cashier is also available: `cashier / cashier123`.

See **[INSTALL.md](INSTALL.md)** for detailed setup and **[DEPLOY.md](DEPLOY.md)**
for production deployment (Windows service / Linux systemd / autostart / network
terminals / backups).

---

## Project Structure

```
kaka-pos-system/
├── run.py                  # Entry point
├── seed.py                 # Optional sample-data loader
├── requirements.txt
├── README.md / INSTALL.md / DEPLOY.md
├── instance/               # SQLite DB + secret key (created at runtime)
├── backups/                # Auto & manual backups (created at runtime)
└── app/
    ├── __init__.py         # App factory, blueprint wiring
    ├── config.py           # Configuration & paths
    ├── database.py         # Connection pool, init, seeding of roles/settings
    ├── schema.sql          # Optimized SQLite schema (indexes, WAL)
    ├── auth.py             # Login/logout/session/password
    ├── api/                # JSON API blueprints (one per domain)
    │   ├── products.py  sales.py  inventory.py  suppliers.py  customers.py
    │   ├── purchases.py  expenses.py  registers.py  reports.py  dashboard.py
    │   ├── zakat.py  backup.py  settings.py  users.py  barcode.py  catalog.py
    ├── utils/              # security, text normalization, stock, audit
    ├── templates/          # login.html, app.html
    └── static/
        ├── css/style.css   # Themed, RTL-aware stylesheet
        ├── i18n/           # en/fr/ar translations
        └── js/             # api, ui, app + per-domain view modules
```

## Architecture Notes

- **Layered API** — each domain is an isolated Flask blueprint exposing a JSON
  API; the frontend is a lightweight vanilla-JS single-page app that consumes it.
- **Single source of truth for stock** — every quantity change flows through
  `utils/stock.adjust_stock`, which updates the product and appends an immutable
  `inventory_movements` row, so the ledger always reconciles.
- **Security** — parameterized SQL everywhere (injection-safe), PBKDF2-SHA256
  password hashing, session cookies (HttpOnly, SameSite), decorator-based
  permission checks, and a comprehensive audit log.
- **Search** — product names are normalized once at write time into a
  `search_blob`; queries are normalized the same way, keeping lookups a fast
  indexed match while remaining accent/case/Arabic/typo tolerant.

## Default Roles & Permissions

| Role | Access |
|------|--------|
| **Administrator** | Everything, including users, backups & restore. |
| **Manager** | All operations & reports, price editing, refunds, discounts, settings. |
| **Cashier** | POS, register, customers, discounts, refunds. |
| **Inventory Employee** | Products, inventory, suppliers, purchases. |

## License

Provided for the requesting business to deploy and operate. Adapt freely for
your store.
