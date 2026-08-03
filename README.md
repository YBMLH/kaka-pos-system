# KAKA POS — Offline Supermarket & Business Management System

A complete, **100% offline** Point of Sale and business management system for
supermarkets, grocery and mini markets, wholesale stores, phone/electronics
shops, clothing and general retail.

**The whole application is one HTML file.** Download it, double-click it, and
you have a working till — no install, no server, no internet, no accounts. All
data stays in that browser on that machine.

👉 **[`docs/index.html`](docs/index.html)** — this is the product.

---

## Run it

**Option A — download and open.** Save `docs/index.html` and double-click it.
Works offline forever after that.

**Option B — host it free on GitHub Pages.** Repo → **Settings → Pages** →
Source: *Deploy from a branch* → Branch **`main`**, folder **`/docs`** → Save.
Your POS is then live at `https://<your-user>.github.io/kaka-pos-system/`.

Sign in with:

```
admin / admin123        (administrator)
cashier / cashier123    (cashier — demo)
```

Sample products are seeded on first run. Change the admin password from the
account menu, then make it yours in **Settings**.

> **Back up your data.** Everything lives in that browser's local storage.
> **Users → Backup & Data → Export Backup** writes a `.json` you can restore
> anywhere. Do this before clearing browser data or moving to another device.
> The same screen shows a storage meter and warns before you run out of space.

---

## What it does

| Area | Highlights |
|------|-----------|
| **Point of Sale** | Barcode scanning, typo-tolerant search, case/box selling, weighed items, custom items, hold & resume, discounts (amount or %), wholesale price breaks, loyalty redemption, cash/card/transfer/mixed/credit, optional receipt printing. |
| **Products** | Full CRUD, scan-to-add, emoji or photo images, categories, cases, wholesale tiers, batches & expiry, barcode labels, CSV import/export. |
| **Inventory** | Real-time stock, alerts, expiry watch (FEFO), write-offs valued at cost, movement ledger, stocktake with variance. |
| **Purchasing** | Purchase orders by piece or case, partial receiving, automatic reordering by supplier, returns to supplier. |
| **People** | Suppliers with balances and payments; customers with credit, purchase history and loyalty points. |
| **Money** | Expenses, cash register open/close with counting, Z-report day-end close, Zakat calculator. |
| **Reports** | Sales, inventory, financial (incl. stock losses), supplier, customer and employee reports with CSV export. |
| **Admin** | Four roles with enforced permissions, audit log, backup/restore, store settings. |

### Details worth knowing

- **Case / box handling.** A product can carry a case size (e.g. 40 per box), a
  separate carton barcode and a case price. Scanning the carton sells a whole
  case; stock is still counted in pieces. Purchase orders can be placed by case
  and receiving converts to pieces, storing cost per piece.
- **Weighed items.** Deli and produce scale labels (in-store EAN-13 embedding
  price or weight) resolve by PLU and add the exact weight and price.
- **Expiry / FEFO.** Batches carry their own expiry; sales always take the
  soonest-to-expire stock first.
- **Mistakes are recoverable.** Void a sale to restore stock and reverse credit,
  loyalty and revenue — the record stays for audit. Damaged goods can be written
  off at cost instead of restocked.
- **Losses hit the P&L.** Damage, expiry, theft, breakage and stocktake
  shortages are valued at cost and subtracted from net profit.
- **Languages.** English, French and Arabic with full RTL, plus light/dark
  themes.
- **Search.** `coca`, `Coca-Cola`, `cocacola` and `كوكا` all find the same
  product — accent-insensitive, Arabic-normalized and typo-tolerant.

---

## Hardware

- **Barcode scanners** — any USB, Bluetooth or wireless scanner works; they act
  as a keyboard. Just scan while the POS search box is focused (`F2`).
- **Camera scanning** — a 📷 button uses the browser's built-in barcode
  detector. Available on Chrome/Edge on Android and ChromeOS; other browsers
  show a clear message and you keep using a scanner.
- **Receipt printers** — receipts print through the normal browser print dialog
  at 58 mm or 80 mm; pick your thermal printer there.

## Keyboard

`F2` focus search · `F4` open payment · `Enter` add scanned item · `Esc` close.

---

## Limits to be aware of

- Data is **per browser, per device**. It is not shared between tills. Use the
  JSON backup to move or merge data.
- Browser storage is roughly **5 MB**. That is thousands of products and sales,
  but product **photos** consume it quickly — emoji placeholders are free.
- Passwords use a lightweight in-browser hash. It keeps staff out of each
  other's accounts; it is not protection against someone with the device and
  developer tools.

---

## Also in this repo

`app/`, `run.py`, `seed.py` — an earlier **Flask + SQLite server** build of the
same idea (multi-terminal, shared database, server-side PDF/Excel). It has
**not** been kept in step with the standalone and lacks the newer features
(cases, batches, tiers, write-offs, void, returns, stocktake, images, scale
barcodes, CSV import, loyalty redemption). Treat `docs/index.html` as the
current product. See [INSTALL.md](INSTALL.md) / [DEPLOY.md](DEPLOY.md) if you
want to run that server build anyway.

## License

Provided for the requesting business to deploy and operate. Adapt freely.
