# Installation Guide — KAKA POS

This guide covers installing and running KAKA POS on **Windows**, **Linux** and
**macOS**. The system is fully offline; only the one-time dependency install
needs internet (or an offline pip cache).

---

## 1. Prerequisites

- **Python 3.9 or newer** (3.11 recommended)
  - Windows: download from <https://www.python.org/downloads/> and tick
    *"Add Python to PATH"* during setup.
  - Linux (Debian/Ubuntu): `sudo apt install python3 python3-pip python3-venv`
  - macOS: `brew install python`
- ~200 MB free disk for the app + dependencies. The database grows with your
  data (roughly 1 GB per ~1–2 million sale lines).

Verify:

```bash
python --version      # or python3 --version
pip --version
```

---

## 2. Get the Files

Copy the `kaka-pos-system` folder to the machine (USB drive, network share, or
`git clone`). No internet is needed after the dependencies are installed.

---

## 3. Create a Virtual Environment (recommended)

Keeps dependencies isolated from the system Python.

**Windows (PowerShell):**
```powershell
cd kaka-pos-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
cd kaka-pos-system
python3 -m venv .venv
source .venv/bin/activate
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Installs Flask, openpyxl (Excel), reportlab (PDF), python-barcode, qrcode and
Pillow. All run locally.

> **Offline install:** on an internet-connected machine run
> `pip download -r requirements.txt -d wheels/`, copy the `wheels/` folder over,
> then `pip install --no-index --find-links wheels -r requirements.txt`.

---

## 5. First Run

```bash
python run.py
```

On first launch the app automatically:
- creates the SQLite database in `instance/kaka_pos.db`,
- creates the four roles and default settings,
- creates the default administrator **admin / admin123**,
- generates and stores a session secret key in `instance/secret.key`.

Open a browser at <http://127.0.0.1:5000>.

### Optional: load sample data

To explore the system pre-filled with categories, suppliers and products across
grocery / electronics / clothing:

```bash
python seed.py
```

This also adds a demo cashier (`cashier / cashier123`). Skip it for a clean
production install — you can add your own products or bulk-import from Excel.

---

## 6. Initial Configuration

After signing in as **admin**:

1. **Change the admin password** — user menu (⚙️) → *Change Password*.
2. **Settings** → set store name, address, phone, currency, tax rate, receipt
   width (58 or 80 mm) and upload your logo.
3. **Users** → create accounts for your managers, cashiers and inventory staff
   with the appropriate roles.
4. **Products** → add products, or download the Excel template
   (Products → Import → *Download Template*), fill it in, and import.
5. **Cash Register** → open a register at the start of each shift.

---

## 7. Choosing the Address / Port

By default the server listens on `127.0.0.1:5000` (this machine only).

```bash
# Make it reachable from other terminals on the local network:
HOST=0.0.0.0 PORT=5000 python run.py          # Linux/macOS
```
```powershell
$env:HOST="0.0.0.0"; $env:PORT="5000"; python run.py   # Windows PowerShell
```

Other terminals then browse to `http://<server-ip>:5000`. See **DEPLOY.md** for
running it as an always-on service.

---

## 8. Barcode Scanners

USB, wireless and Bluetooth barcode scanners work out of the box — they act as a
keyboard. Just focus the POS search box (it auto-focuses) and scan; an exact
barcode match is added to the cart instantly. No drivers or configuration
needed.

---

## 9. Receipt Printers

Thermal receipts are generated as PDF sized for **58 mm** or **80 mm** paper
(set in Settings). Printing uses the browser's print dialog / your OS printer —
select your thermal printer there. Any ESC/POS thermal printer installed as a
system printer works.

---

## 10. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `python: command not found` | Use `python3`, or reinstall Python with PATH enabled. |
| `pip install` fails on Pillow/reportlab | Upgrade pip: `pip install --upgrade pip`. On Linux install build tools: `sudo apt install build-essential python3-dev`. |
| Port 5000 already in use | Start with a different port: `PORT=5050 python run.py`. |
| Forgot admin password | See DEPLOY.md → *Password recovery*. |
| Browser shows "connection refused" | Ensure `python run.py` is still running and you used the right host/port. |

---

Continue to **[DEPLOY.md](DEPLOY.md)** for production deployment, autostart and
backups.
