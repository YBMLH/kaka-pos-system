# KAKA POS — Offline Supermarket & Business Management System

A complete, **100% offline** Point of Sale and business management system for
supermarkets, grocery and mini markets, wholesale stores, phone/electronics
shops, clothing and general retail.

**The whole application is one HTML file.** Download it, double-click it, and
you have a working till — no install, no server, no internet, no accounts. All
data stays in that browser on that machine.

👉 **[`docs/index.html`](docs/index.html)** — this is the product.
📄 **[QUICKSTART.md](QUICKSTART.md)** — hand this to the shop; it is written for
staff, not developers.

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

On first run a **setup wizard** walks the owner through their shop name,
currency and whether they charge tax, connecting a data file, replacing the
default admin password,
and clearing the example products. It cannot be skipped and never reappears.
(Re-run it any time from **Settings → Re-run setup wizard**.)

### Save to a file on the PC (recommended)

Go to **Users → Backup & Data → Create a data file…**, pick where to save it
(e.g. `D:\KakaPOS\shop-data.json`), and from then on the app **writes that file
after every change** — every sale, price edit and stock movement. Reopen the app
later and it reconnects to the same file automatically.

The top bar always shows where your data is going:

| Chip | Meaning |
|------|---------|
| 💾 **Saved** / filename | Writing to your file — all good |
| 💾 **Browser only** | No file connected; data is only in this browser |
| ⚠ **Reconnect file** | The browser needs permission again — click to restore |
| ⚠ **Not saved** | A write failed; the message says why |

Because it is a normal file you can put it on a USB stick, a shared folder, or
anything your usual PC backup already copies. **Open an existing data file…**
loads it back on any machine.

> Writing files needs **Chrome or Edge on desktop** (Chrome 86+, so Chrome 109
> — the last release for Windows 7 — is fine). Other browsers keep using
> browser storage — the app says so, and Export/Import backups still work.
> A copy is always kept in the browser as a fallback, so a disconnected or
> unsupported file never loses your data.
>
> On a browser that cannot own a file, the app instead hands the browser a
> dated backup file every N sales and at register close (**Settings →
> Automatic backup file every N sales**), so real files still land on the disk
> without anyone having to remember.

---

## What it does

| Area | Highlights |
|------|-----------|
| **Point of Sale** | Barcode scanning, typo-tolerant search, case/box selling, weighed items, custom items, hold & resume, discounts (amount or %), wholesale price breaks, loyalty redemption, cash/card/transfer/mixed/credit, optional receipt printing. |
| **Products** | Full CRUD, scan-to-add, emoji or photo images, categories, cases, wholesale tiers, batches & expiry, barcode labels, CSV import/export. |
| **Inventory** | Real-time stock, alerts, expiry watch (FEFO), write-offs valued at cost, movement ledger, stocktake with variance. |
| **Purchasing** | Purchase orders by piece or case, partial receiving, automatic reordering by supplier, returns to supplier. |
| **People** | Suppliers with balances and payments; customers with credit, purchase history and loyalty points. |
| **Money** | Expenses, cash register open/close with counting, cash in/out of the drawer (owner withdrawals, suppliers paid at the door, till expenses), Z-report day-end close, Zakat calculator. |
| **Reports** | Sales, inventory, financial (incl. stock losses), supplier, customer and employee reports with CSV export. |
| **Admin** | Four roles with enforced permissions, audit log, backup/restore, store settings. |

### Details worth knowing

- **Costs that move.** A delivery of something already on the shelf rarely
  arrives at the old price, so each delivery keeps its own cost as a layer and
  stock is sold oldest first (FIFO). The boxes bought at 60 stay worth 60 and
  are sold at 60 until they run out; only then does the shop start selling the
  ones that cost 80. The shelf price is a separate decision — the same item can
  sell for one price whatever each piece cost to buy. Sales, voids, refunds,
  write-offs, stocktake shortages and the inventory valuation all follow those
  layers, and a void puts the exact layers it consumed back. See what is on the
  shelf and at what price in **Products → 💰 Wholesale → What this stock cost
  you**. After receiving, the app shows what the new price does to your margin
  and offers the shelf price that restores it, applied only where you tick.
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
- **Scan from anywhere.** A scanner is just a fast keyboard, so a scan made on
  any screen jumps to the till and adds the item to the basket — including
  while a search box has focus, which is where a cashier usually is. A burst
  is only taken over from a field when it could not have been typed by hand
  (8+ characters, every one under 60 ms), and whatever was in the field is put
  back. Slow typing, an open dialog and the lock screen are never intercepted,
  and the basket survives moving between screens.
- **The drawer is a ledger.** Cash that leaves or enters the till without being
  a sale is recorded with its reason and who did it. An owner withdrawal moves
  money without touching profit; a supplier paid in cash or a till expense also
  creates an expense record. Closing the register and the Z-report both count
  these movements.
- **Keyboard layouts.** A scanner types as though the computer were set to a
  US keyboard, so on an AZERTY or Arabic layout every digit arrives as a
  symbol. Codes that match nothing are retried through a layout translation
  before being given up on, so scanning works either way — and a code that
  genuinely contains a dash still matches itself first. **Settings → Test the
  barcode scanner** reports what was sent versus what was read.
- **Old machines are handled.** The app checks what the browser can actually
  do and adapts: no emoji font (Windows 7 and earlier) switches every icon to
  plain words and shows a product's initial instead of a picture; no
  `color-mix()` (Chrome 109, Firefox 52) restores solid button colours; no
  flexbox `gap` (anything pre-2020) falls back to margins. Force either icon
  style in **Settings → Icons**.
- **Storage has a floor, not a cliff.** Without a data file the browser gives
  about 5 MB — roughly 1,500 products and a month of sales. The app warns at
  75%, and **Backup & Data → Archive sales older than 90 days / 1 year** writes
  them to a file you keep and clears the space.
- **Tax is optional.** New shops start with **no tax** — the price on the shelf
  is exactly what the customer pays, and no tax line appears on screen, on the
  receipt or in the reports. Shops that do charge it turn it on in
  **Settings → Sales tax / VAT** and choose whether shelf prices already
  include the tax (retail) or it is added at the till (wholesale).
- **Losses hit the P&L.** Damage, expiry, theft, breakage and stocktake
  shortages are valued at cost and subtracted from net profit.
- **Languages.** Set the language to **Français** and the whole app is French —
  every screen, dialog, message, table, printed receipt and Z-report, not just
  the menus. Arabic covers the navigation and till with full RTL; the rest of
  its screens stay in English. Translation happens at the single point every
  piece of text passes through on its way to the screen, so nothing had to be
  rewired call site by call site — and anything the app does not recognise
  (product names, notes, amounts) is left exactly as typed.
- **Look and feel.** A flat, uniform surface system: one radius scale, one
  border, one shadow, and the accent colour used the same way everywhere. The
  till lists products as full-width rows — name, stock, barcode, price and one
  round add button per line, which reads far better than tiles for long Arabic
  and French names (**▦ Tiles** switches back, remembered per till). The cart
  carries a four-button quick row — clear, hold, held sales, reprint — above a
  single large charge button. Blur is now limited to the sidebar, top bar and
  dialogs; everything inside the page is a solid card, which also renders
  faster on modest till hardware. Underneath it remains the same Apple-style
  frosted glass: layered translucent surfaces
  over a soft mesh background, SF typography and Apple system accents. Blur is
  limited to large structural surfaces (sidebar, top bar, cards, cart, dialogs)
  and never applied to list rows or product tiles, so it stays smooth on modest
  till hardware. **Settings → Reduce transparency** turns every surface solid
  for weak machines or harsh shop lighting, and the OS
  `prefers-reduced-transparency` / `prefers-reduced-motion` settings are
  respected automatically.
- **Search.** `coca`, `Coca-Cola`, `cocacola` and `كوكا` all find the same
  product — accent-insensitive, Arabic-normalized and typo-tolerant.

---

## Which browser

| Machine | Browser | Data file | Notes |
|---|---|---|---|
| Windows 10 / 11, current | Chrome or Edge | ✅ automatic | Everything on |
| **Windows 7** | **Chrome 109** (last for Win7) | ✅ automatic | Icons switch to words — Win7's emoji font is incomplete |
| Windows XP | Firefox 52.9 ESR (last for XP) | ❌ | Words instead of icons, automatic backup files instead of a data file |
| Firefox, any version | Firefox | ❌ | Browser storage + backups |

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

In-app help lives behind the **❓** button in the top bar.

## Delivering to a shop

1. Copy `docs/index.html` to the till (a desktop shortcut helps) and print
   [QUICKSTART.md](QUICKSTART.md).
2. Sign in as `admin` / `admin123` and complete the setup wizard **with the
   owner present** — they should choose the password and the data file location.
3. Load their catalogue: scan items in one by one, or **Products → ⬆ Import CSV**.
4. Show them the three things that matter daily: scan → **Charge**, the green
   save chip, and **Close Register → Print Z-Report**.
5. Agree a weekly routine of copying the data file to a USB stick.

---

## Limits to be aware of

- With a data file connected, your data is a normal file you control. Without
  one, it lives only in that browser on that device.
- The data file is **one till's data**. Two tills writing the same file at the
  same time would overwrite each other — give each its own file.
- Browser storage (the fallback copy) is roughly **5 MB**. Product **photos**
  consume it quickly; emoji placeholders are free. The data file itself is not
  limited this way.
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
