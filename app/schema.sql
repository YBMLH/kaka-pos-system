-- ===========================================================================
-- KAKA POS — SQLite schema
-- Optimized for 50,000+ products and 100,000+ sales records.
-- Uses WAL journaling, foreign keys, and targeted indexes for fast lookups.
-- ===========================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Roles & Users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,          -- administrator, manager, cashier, inventory
    label       TEXT NOT NULL,
    permissions TEXT NOT NULL DEFAULT '[]'     -- JSON array of permission keys
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role_id       INTEGER NOT NULL REFERENCES roles(id),
    email         TEXT DEFAULT '',
    phone         TEXT DEFAULT '',
    is_active     INTEGER NOT NULL DEFAULT 1,
    language      TEXT NOT NULL DEFAULT 'en',
    theme         TEXT NOT NULL DEFAULT 'light',
    last_login    TEXT,
    reset_token   TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);

-- ---------------------------------------------------------------------------
-- Catalog: categories, brands, suppliers, products
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    name_ar   TEXT DEFAULT '',
    name_fr   TEXT DEFAULT '',
    parent_id INTEGER REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS brands (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name   TEXT NOT NULL,
    contact_person TEXT DEFAULT '',
    phone1         TEXT DEFAULT '',
    phone2         TEXT DEFAULT '',
    whatsapp       TEXT DEFAULT '',
    email          TEXT DEFAULT '',
    website        TEXT DEFAULT '',
    address        TEXT DEFAULT '',
    city           TEXT DEFAULT '',
    country        TEXT DEFAULT '',
    tax_number     TEXT DEFAULT '',
    category       TEXT DEFAULT 'Miscellaneous',
    balance        REAL NOT NULL DEFAULT 0,   -- positive = we owe supplier
    notes          TEXT DEFAULT '',
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(company_name);

CREATE TABLE IF NOT EXISTS products (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode        TEXT UNIQUE,
    sku            TEXT,
    name_en        TEXT NOT NULL DEFAULT '',
    name_ar        TEXT NOT NULL DEFAULT '',
    name_fr        TEXT NOT NULL DEFAULT '',
    search_blob    TEXT NOT NULL DEFAULT '',   -- normalized names for fast typo/accent search
    category_id    INTEGER REFERENCES categories(id),
    brand_id       INTEGER REFERENCES brands(id),
    supplier_id    INTEGER REFERENCES suppliers(id),
    purchase_price REAL NOT NULL DEFAULT 0,
    selling_price  REAL NOT NULL DEFAULT 0,
    tax_rate       REAL NOT NULL DEFAULT 0,
    quantity       REAL NOT NULL DEFAULT 0,
    min_stock      REAL NOT NULL DEFAULT 0,
    unit           TEXT NOT NULL DEFAULT 'pcs',
    image          TEXT DEFAULT '',
    expiry_date    TEXT,
    batch_number   TEXT DEFAULT '',
    notes          TEXT DEFAULT '',
    is_archived    INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_products_barcode  ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_sku       ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_search    ON products(search_blob);
CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_archived  ON products(is_archived);

-- ---------------------------------------------------------------------------
-- Customers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    phone       TEXT DEFAULT '',
    address     TEXT DEFAULT '',
    city        TEXT DEFAULT '',
    loyalty_pts INTEGER NOT NULL DEFAULT 0,
    credit      REAL NOT NULL DEFAULT 0,      -- outstanding customer credit (they owe us)
    notes       TEXT DEFAULT '',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);

-- ---------------------------------------------------------------------------
-- Sales
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no     TEXT NOT NULL UNIQUE,
    user_id        INTEGER REFERENCES users(id),
    customer_id    INTEGER REFERENCES customers(id),
    register_id    INTEGER REFERENCES registers(id),
    subtotal       REAL NOT NULL DEFAULT 0,
    discount       REAL NOT NULL DEFAULT 0,
    tax            REAL NOT NULL DEFAULT 0,
    total          REAL NOT NULL DEFAULT 0,
    cost_total     REAL NOT NULL DEFAULT 0,
    profit         REAL NOT NULL DEFAULT 0,
    paid           REAL NOT NULL DEFAULT 0,
    change_due     REAL NOT NULL DEFAULT 0,
    payment_method TEXT NOT NULL DEFAULT 'cash',   -- cash, card, transfer, mixed, credit
    payment_detail TEXT DEFAULT '{}',              -- JSON breakdown for mixed payments
    status         TEXT NOT NULL DEFAULT 'completed', -- completed, held, cancelled, refunded
    note           TEXT DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_sales_created ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_user    ON sales(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_status  ON sales(status);
CREATE INDEX IF NOT EXISTS idx_sales_receipt ON sales(receipt_no);

CREATE TABLE IF NOT EXISTS sale_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id       INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id    INTEGER REFERENCES products(id),
    name          TEXT NOT NULL,
    barcode       TEXT DEFAULT '',
    quantity      REAL NOT NULL DEFAULT 1,
    unit_price    REAL NOT NULL DEFAULT 0,
    purchase_price REAL NOT NULL DEFAULT 0,
    discount      REAL NOT NULL DEFAULT 0,
    tax_rate      REAL NOT NULL DEFAULT 0,
    line_total    REAL NOT NULL DEFAULT 0,
    refunded_qty  REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_saleitems_sale    ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_saleitems_product ON sale_items(product_id);

-- Held (parked) sales — stored as JSON so any terminal can resume them.
CREATE TABLE IF NOT EXISTS held_sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    label      TEXT NOT NULL DEFAULT '',
    user_id    INTEGER REFERENCES users(id),
    cart_json  TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ---------------------------------------------------------------------------
-- Purchases (from suppliers)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchases (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reference      TEXT NOT NULL UNIQUE,
    supplier_id    INTEGER REFERENCES suppliers(id),
    user_id        INTEGER REFERENCES users(id),
    invoice_number TEXT DEFAULT '',
    subtotal       REAL NOT NULL DEFAULT 0,
    total          REAL NOT NULL DEFAULT 0,
    paid           REAL NOT NULL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'draft',  -- draft, ordered, partial, received, cancelled
    note           TEXT DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status   ON purchases(status);

CREATE TABLE IF NOT EXISTS purchase_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id  INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    product_id   INTEGER REFERENCES products(id),
    name         TEXT NOT NULL,
    quantity     REAL NOT NULL DEFAULT 0,
    received_qty REAL NOT NULL DEFAULT 0,
    cost         REAL NOT NULL DEFAULT 0,
    line_total   REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_purchaseitems_purchase ON purchase_items(purchase_id);

-- Supplier payments ledger
CREATE TABLE IF NOT EXISTS supplier_payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    amount      REAL NOT NULL DEFAULT 0,
    method      TEXT NOT NULL DEFAULT 'cash',
    note        TEXT DEFAULT '',
    user_id     INTEGER REFERENCES users(id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ---------------------------------------------------------------------------
-- Inventory movements (single source of truth for every stock change)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_movements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    change_qty  REAL NOT NULL DEFAULT 0,         -- +in / -out
    balance     REAL NOT NULL DEFAULT 0,         -- resulting stock level
    reason      TEXT NOT NULL,                   -- sale, purchase, adjustment, damage, loss, expired, return, transfer, count
    ref_type    TEXT DEFAULT '',
    ref_id      INTEGER,
    note        TEXT DEFAULT '',
    user_id     INTEGER REFERENCES users(id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_movements_product ON inventory_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_movements_created ON inventory_movements(created_at);

-- ---------------------------------------------------------------------------
-- Cash registers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER REFERENCES users(id),
    opening_cash  REAL NOT NULL DEFAULT 0,
    closing_cash  REAL,
    counted_cash  REAL,
    expected_cash REAL,
    difference    REAL,
    status        TEXT NOT NULL DEFAULT 'open',   -- open, closed
    opened_at     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    closed_at     TEXT,
    note          TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_registers_status ON registers(status);

-- ---------------------------------------------------------------------------
-- Expenses
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    category   TEXT NOT NULL DEFAULT 'Miscellaneous',
    amount     REAL NOT NULL DEFAULT 0,
    note       TEXT DEFAULT '',
    user_id    INTEGER REFERENCES users(id),
    spent_on   TEXT NOT NULL DEFAULT (date('now','localtime')),
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(spent_on);

-- ---------------------------------------------------------------------------
-- Activity / audit log
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id),
    username   TEXT DEFAULT '',
    action     TEXT NOT NULL,
    entity     TEXT DEFAULT '',
    entity_id  INTEGER,
    detail     TEXT DEFAULT '',
    ip         TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_logs_created ON activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_user    ON activity_logs(user_id);

-- ---------------------------------------------------------------------------
-- Key/value settings + backup registry
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS backups (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    filename   TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    kind       TEXT NOT NULL DEFAULT 'manual',  -- manual, daily, weekly
    checksum   TEXT DEFAULT '',
    verified   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
