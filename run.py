#!/usr/bin/env python3
"""KAKA POS — application entry point.

Runs a fully offline POS + business management server.

Usage:
    python run.py            # start on http://127.0.0.1:5000
    HOST=0.0.0.0 PORT=8080 python run.py
"""
import os

from app import create_app
from app.database import init_db

app = create_app()


def main() -> None:
    # Ensure the database + default admin exist before serving.
    with app.app_context():
        init_db()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"  KAKA POS running at http://{host}:{port}  (offline mode)")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
