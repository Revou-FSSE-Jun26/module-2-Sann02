# helper/seed.py
# Script untuk seed data Users, Categories, dan Products.
# Data produk diambil dari hasil scraping Tokopedia (kategori Komputer & Laptop)
# yang tersimpan di helper/data/tokopedia_komputer_laptop.csv
#
# Jalankan: python -m helper.seed

import csv
import os
import random

from app import app
from extensions import db
from models import User, Category, Product


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PRODUCTS_CSV = os.path.join(DATA_DIR, "tokopedia_komputer_laptop.csv")


# ---------------------------------------------------------------------------
# Kategori toko. Setiap produk hasil scrape dipetakan ke salah satu kategori
# ini berdasarkan kata kunci pada nama produknya (lihat classify_category).
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"name": "Laptop", "description": "Laptop dan notebook"},
    {"name": "Mouse", "description": "Mouse gaming dan kantor"},
    {"name": "Keyboard", "description": "Keyboard dan combo gaming"},
    {"name": "Tas & Sleeve Laptop", "description": "Tas, ransel, dan sleeve pelindung laptop"},
    {"name": "Aksesoris Komputer", "description": "Adapter, hub, kabel, dan aksesoris lainnya"},
    {"name": "Komponen & Pendingin", "description": "RAM, cooler, dan komponen internal"},
]


def classify_category(name: str) -> str:
    """Tentukan kategori toko dari nama produk hasil scrape."""
    lower = name.lower()

    # Laptop utuh: nama diawali merek laptop, atau mengandung penanda unit resmi.
    # Hindari false-positive dari aksesoris yang menyebut "macbook/laptop" (hub, charger, dll).
    if lower.startswith("apple macbook") or "laptop resmi" in lower or "macos laptop" in lower:
        return "Laptop"
    if "keyboard" in lower or "combo" in lower:
        return "Keyboard"
    if "mouse" in lower and "mousepad" not in lower and "mouse pad" not in lower:
        return "Mouse"
    if any(k in lower for k in ["tas", "backpack", "ransel", "sleeve", "sling", "standbag", "handbag", "bag"]):
        return "Tas & Sleeve Laptop"
    if any(k in lower for k in ["ram", "cooler", "pendingin", "cooling", "heatpipe"]):
        return "Komponen & Pendingin"
    # sisanya: adapter, hub, charger, wifi, kabel, mousepad, speaker, joystick
    return "Aksesoris Komputer"


def build_description(row: dict, category_name: str) -> str:
    """Buat deskripsi singkat dari metadata toko hasil scrape."""
    shop = row.get("shop_name", "").strip()
    city = row.get("shop_city", "").strip()
    rating = row.get("rating", "").strip()

    parts = [f"{category_name} asli Tokopedia."]
    if shop:
        lokasi = f" ({city})" if city else ""
        parts.append(f"Dijual oleh {shop}{lokasi}.")
    if rating:
        parts.append(f"Rating toko {rating}.")
    return " ".join(parts)


def load_products_from_csv():
    """Baca produk hasil scrape dari CSV dan siapkan untuk di-seed."""
    products = []
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            price_raw = (row.get("price") or "").strip()
            if not name or not price_raw:
                continue

            try:
                price = float(price_raw)
            except ValueError:
                continue

            category_name = classify_category(name)
            products.append({
                "name": name,
                "price": price,
                "category": category_name,
                "description": build_description(row, category_name),
                # stok acak tapi deterministik agar hasil seed konsisten
                "stock_quantity": random.randint(5, 80),
            })
    return products


def seed_users():
    """Seed data pengguna"""
    users = [
        {"username": "admin", "email": "admin@email.com", "password": "admin123", "role": "admin"},
        {"username": "ikhsanfebrian", "email": "ikhsan@email.com", "password": "password123", "role": "user"},
        {"username": "sari", "email": "sari@email.com", "password": "password123", "role": "user"},
    ]

    for data in users:
        existing = User.query.filter_by(email=data['email']).first()
        if not existing:
            user = User(username=data['username'], email=data['email'], role=data['role'])
            user.set_password(data['password'])
            db.session.add(user)
            print(f"  + User '{data['username']}' created")
        else:
            print(f"  - User '{data['username']}' already exists, skipped")

    db.session.commit()


def seed_categories():
    """Seed data kategori"""
    for data in CATEGORIES:
        existing = Category.query.filter_by(name=data['name']).first()
        if not existing:
            category = Category(name=data['name'], description=data['description'])
            db.session.add(category)
            print(f"  + Category '{data['name']}' created")
        else:
            print(f"  - Category '{data['name']}' already exists, skipped")

    db.session.commit()


def seed_products():
    """Seed data produk dari hasil scraping Tokopedia"""
    products = load_products_from_csv()
    print(f"  Loaded {len(products)} products from {os.path.basename(PRODUCTS_CSV)}")

    # cache kategori agar tidak query berulang
    category_map = {c.name: c.id for c in Category.query.all()}

    created = 0
    skipped = 0
    for data in products:
        existing = Product.query.filter_by(name=data['name']).first()
        if existing:
            skipped += 1
            continue

        category_id = category_map.get(data['category'])
        if not category_id:
            print(f"  ! Category '{data['category']}' not found, skipping product '{data['name'][:40]}...'")
            continue

        product = Product(
            name=data['name'],
            price=data['price'],
            category_id=category_id,
            description=data['description'],
            stock_quantity=data['stock_quantity'],
        )
        db.session.add(product)
        created += 1

    db.session.commit()
    print(f"  + {created} products created, {skipped} already existed (skipped)")


def run():
    # seed deterministik supaya stock_quantity konsisten antar run
    random.seed(42)

    with app.app_context():
        print("\n=== Seeding Database ===\n")

        print("[Users]")
        seed_users()

        print("\n[Categories]")
        seed_categories()

        print("\n[Products]")
        seed_products()

        print("\n=== Seeding Complete ===\n")


if __name__ == '__main__':
    run()
