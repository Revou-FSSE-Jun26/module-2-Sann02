# helper/backup_db.py
# Backup tabel categories, products, orders, order_items ke CSV sebelum reset/seed.
# Jalankan: python -m helper.backup_db <label>
#   -> helper/_backup_<label>_<tabel>_<timestamp>.csv

import csv
import datetime
import os
import sys

from app import app
from extensions import db

TABLES = ("categories", "products", "orders", "order_items")


def run(label):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.dirname(__file__)
    with app.app_context():
        print(f"DB host: {db.engine.url.host}")
        for table in TABLES:
            res = db.session.execute(db.text(f"SELECT * FROM {table} ORDER BY id"))
            rows = res.fetchall()
            path = os.path.join(out_dir, f"_backup_{label}_{table}_{ts}.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(res.keys())
                w.writerows(rows)
            print(f"  backup {table:<12} {len(rows):>4} rows -> {os.path.basename(path)}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "db")
