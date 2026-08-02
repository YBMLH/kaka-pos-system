# Deployment Guide — KAKA POS

This guide covers running KAKA POS reliably in a real store: as an always-on
service, serving multiple terminals on the local network, backups, and
maintenance. Everything remains **fully offline**.

---

## 1. Production Web Server

`python run.py` uses Flask's built-in server, which is fine for a single
till but not ideal for a busy multi-terminal store. For production use a
WSGI server — **waitress** is the simplest choice and works identically on
Windows and Linux.

```bash
pip install waitress
```

Create `serve.py` in the project root:

```python
from waitress import serve
from app import create_app
from app.database import init_db

app = create_app()
with app.app_context():
    init_db()

# threads: raise for more concurrent terminals
serve(app, host="0.0.0.0", port=5000, threads=8)
```

Run it with `python serve.py`. SQLite in WAL mode (already enabled) handles
multiple concurrent cashiers on one machine comfortably.

---

## 2. Single-Machine vs. Networked Terminals

- **Single till** — run on the till PC, browse to `http://127.0.0.1:5000`.
- **Multiple terminals** — run the server on one "server" PC with
  `host=0.0.0.0`. Every other till opens `http://<server-ip>:5000` in a
  browser. Only the server PC holds the database; give it a **static local IP**
  (e.g. `192.168.1.10`) so the address never changes.

Find the server IP: `ipconfig` (Windows) / `ip addr` (Linux).

---

## 3. Autostart as a Service

### Windows (Task Scheduler)

1. Open **Task Scheduler → Create Task**.
2. General: *Run whether user is logged on or not*, *Run with highest privileges*.
3. Triggers: **At startup**.
4. Actions: Start a program →
   - Program: `C:\path\to\kaka-pos-system\.venv\Scripts\python.exe`
   - Arguments: `serve.py`
   - Start in: `C:\path\to\kaka-pos-system`
5. Save. The POS server now starts with Windows.

Alternatively use **NSSM** (Non-Sucking Service Manager) to install it as a true
Windows service:
```
nssm install KakaPOS "C:\path\.venv\Scripts\python.exe" "C:\path\serve.py"
nssm set KakaPOS AppDirectory "C:\path\kaka-pos-system"
nssm start KakaPOS
```

### Linux (systemd)

Create `/etc/systemd/system/kaka-pos.service`:

```ini
[Unit]
Description=KAKA POS
After=network.target

[Service]
Type=simple
User=pos
WorkingDirectory=/opt/kaka-pos-system
ExecStart=/opt/kaka-pos-system/.venv/bin/python serve.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kaka-pos
sudo systemctl status kaka-pos
```

### Kiosk mode (optional)

Launch Chrome/Edge in kiosk mode so the till boots straight into the POS:
```
chrome.exe --kiosk --app=http://127.0.0.1:5000
```

---

## 4. Security Hardening

- **Change the default admin password** on day one.
- Set a strong, persistent secret key (optional — one is auto-generated and
  stored in `instance/secret.key`). To pin your own:
  ```bash
  SECRET_KEY="your-long-random-string" python serve.py
  ```
- Create individual accounts per employee (never share logins) — the audit log
  attributes every action to a user.
- Keep the server PC physically secure; the SQLite file *is* your business data.
- The system uses parameterized SQL (injection-safe), PBKDF2 password hashing,
  and HttpOnly session cookies out of the box.

---

## 5. Backups

Automatic **daily** and **weekly** backups run when the first user logs in each
day (toggle in Settings → *Auto Backup*). Files land in `backups/` and are
checksum-verified.

- **Manual backup:** Users → Backups → *Create Backup*.
- **Verify:** each backup can be checksum- and integrity-verified from the UI.
- **Restore:** Users → Backups → *Restore* (snapshots current data first, then
  replaces the DB — restart the app afterward).
- **Off-site copy:** periodically copy the `backups/` folder (and/or
  `instance/kaka_pos.db`) to a USB drive or NAS. This is your disaster recovery.

> A full offline backup is simply the `instance/` and `backups/` folders. Copy
> them while the server is stopped for a guaranteed-consistent snapshot, or use
> the in-app backup (which is consistent even while running).

---

## 6. Password Recovery (offline)

If an administrator password is lost and no other admin exists, reset it from a
Python shell on the server:

```bash
python - <<'PY'
from app import create_app
from app.database import execute
from app.utils.security import hash_password
app = create_app()
with app.app_context():
    execute("UPDATE users SET password_hash=?, is_active=1 WHERE username='admin'",
            (hash_password("newpassword123"),))
print("admin password reset to: newpassword123")
PY
```

For non-admin users, an administrator can reset passwords from **Users → Edit**.

---

## 7. Maintenance

- **Database size:** SQLite handles millions of rows. If it grows very large,
  run `VACUUM` occasionally during downtime:
  ```bash
  python - <<'PY'
  import sqlite3; c=sqlite3.connect("instance/kaka_pos.db"); c.execute("VACUUM"); c.close()
  PY
  ```
- **Logs:** the activity log is capped in the UI to the latest 500 entries but
  retained fully in the database for auditing.
- **Updates:** replace the `app/` code with a new version; the schema uses
  `CREATE TABLE IF NOT EXISTS` so existing data is preserved. Always back up
  before updating.

---

## 8. Recommended Store Setup Checklist

- [ ] Install Python + dependencies on the server PC
- [ ] Set a static local IP on the server PC
- [ ] Configure autostart (Task Scheduler / systemd)
- [ ] Change admin password; create employee accounts
- [ ] Fill in Settings (store info, currency, tax, receipt size, logo)
- [ ] Import product catalog via Excel
- [ ] Connect & test barcode scanner and thermal printer
- [ ] Confirm automatic backups run; set up a weekly USB/NAS copy
- [ ] Train staff: opening/closing the register, POS, refunds, stock counts

Your KAKA POS is now ready for daily business.
