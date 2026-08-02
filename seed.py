#!/usr/bin/env python3
"""Optional seed script — populates realistic starter data for a new install.

This is a convenience for first-time setup and demonstrations. It is NOT
required to run the system. Run once against an empty database:

    python seed.py

It creates categories, brands, a few suppliers, sample products across retail
segments (grocery, electronics, clothing) and one demo cashier user.
"""
import random

from app import create_app
from app.database import execute, get_db, init_db, query
from app.utils.security import hash_password
from app.utils.text import build_search_blob

CATEGORIES = ["Beverages", "Dairy", "Bakery", "Snacks", "Cleaning", "Cosmetics",
              "Electronics", "Phones", "Clothing", "Fruits & Vegetables"]
BRANDS = ["Coca Cola", "Nestle", "Samsung", "Apple", "Nike", "Danone", "P&G", "Generic"]

SUPPLIERS = [
    ("Atlas Distribution", "Beverages", "0522110011", "atlas@example.com"),
    ("Nord Food Supply", "Dairy", "0522220022", "nord@example.com"),
    ("TechnoPro Import", "Electronics", "0522330033", "techno@example.com"),
    ("Fashion House", "Miscellaneous", "0522440044", "fashion@example.com"),
]

PRODUCTS = [
    # (name_en, name_fr, name_ar, category, brand, cost, price, tax, qty, min)
    ("Coca Cola 1L", "Coca Cola 1L", "كوكا كولا 1 لتر", "Beverages", "Coca Cola", 6, 9, 20, 200, 40),
    ("Mineral Water 1.5L", "Eau Minérale 1.5L", "ماء معدني 1.5 لتر", "Beverages", "Generic", 2, 4, 20, 300, 60),
    ("Fresh Milk 1L", "Lait Frais 1L", "حليب طازج 1 لتر", "Dairy", "Danone", 7, 11, 20, 120, 30),
    ("Yogurt Pack x4", "Yaourt x4", "زبادي 4 حبات", "Dairy", "Danone", 8, 13, 20, 90, 20),
    ("White Bread", "Pain Blanc", "خبز أبيض", "Bakery", "Generic", 1.5, 3, 0, 80, 20),
    ("Potato Chips 150g", "Chips 150g", "رقائق البطاطس 150غ", "Snacks", "Generic", 5, 8.5, 20, 150, 30),
    ("Dish Soap 500ml", "Liquide Vaisselle 500ml", "سائل غسيل 500مل", "Cleaning", "P&G", 9, 15, 20, 60, 15),
    ("Shampoo 400ml", "Shampooing 400ml", "شامبو 400مل", "Cosmetics", "P&G", 18, 29, 20, 45, 10),
    ("USB-C Cable 1m", "Câble USB-C 1m", "كابل USB-C 1م", "Electronics", "Generic", 15, 35, 20, 70, 15),
    ("Wireless Earbuds", "Écouteurs sans fil", "سماعات لاسلكية", "Electronics", "Samsung", 180, 299, 20, 25, 5),
    ("Samsung Galaxy A15", "Samsung Galaxy A15", "سامسونج جالاكسي A15", "Phones", "Samsung", 1400, 1899, 20, 12, 3),
    ("Phone Case", "Coque Téléphone", "غطاء هاتف", "Phones", "Generic", 12, 30, 20, 100, 20),
    ("Cotton T-Shirt", "T-Shirt Coton", "قميص قطني", "Clothing", "Nike", 45, 89, 20, 60, 10),
    ("Running Shoes", "Chaussures de Sport", "أحذية رياضية", "Clothing", "Nike", 210, 349, 20, 20, 5),
    ("Bananas (kg)", "Bananes (kg)", "موز (كغ)", "Fruits & Vegetables", "Generic", 6, 10, 0, 150, 30),
    ("Tomatoes (kg)", "Tomates (kg)", "طماطم (كغ)", "Fruits & Vegetables", "Generic", 4, 7, 0, 120, 25),
]


def run():
    app = create_app()
    with app.app_context():
        init_db()
        db = get_db()
        if query("SELECT COUNT(*) AS c FROM products", one=True)["c"] > 0:
            print("Database already has products — skipping seed.")
            return

        cat_ids, brand_ids = {}, {}
        for c in CATEGORIES:
            cat_ids[c] = execute("INSERT INTO categories (name) VALUES (?)", (c,))
        for b in BRANDS:
            brand_ids[b] = execute("INSERT INTO brands (name) VALUES (?)", (b,))

        sup_ids = []
        for name, category, phone, email in SUPPLIERS:
            sup_ids.append(execute(
                "INSERT INTO suppliers (company_name, category, phone1, email) VALUES (?,?,?,?)",
                (name, category, phone, email)))

        barcode_base = 6111000000000
        for i, (en, fr, ar, cat, brand, cost, price, tax, qty, mn) in enumerate(PRODUCTS):
            barcode = str(barcode_base + i * 7)
            execute(
                "INSERT INTO products (barcode, sku, name_en, name_fr, name_ar, search_blob, "
                "category_id, brand_id, supplier_id, purchase_price, selling_price, tax_rate, "
                "quantity, min_stock, unit) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (barcode, f"SKU{i+1:04d}", en, fr, ar, build_search_blob(en, fr, ar, barcode),
                 cat_ids[cat], brand_ids[brand], random.choice(sup_ids), cost, price, tax, qty, mn,
                 "kg" if "(kg)" in en else "pcs"))

        # Demo cashier
        cashier_role = query("SELECT id FROM roles WHERE name='cashier'", one=True)["id"]
        if not query("SELECT id FROM users WHERE username='cashier'", one=True):
            execute("INSERT INTO users (username, full_name, password_hash, role_id) VALUES (?,?,?,?)",
                    ("cashier", "Demo Cashier", hash_password("cashier123"), cashier_role))

        print(f"Seeded {len(PRODUCTS)} products, {len(CATEGORIES)} categories, "
              f"{len(SUPPLIERS)} suppliers.")
        print("Users: admin/admin123 (administrator), cashier/cashier123 (cashier)")


if __name__ == "__main__":
    run()
