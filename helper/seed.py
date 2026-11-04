# helper/seed.py
# Script untuk seed data Users, Categories, dan Products.
# Data produk diambil dari hasil scraping Tokopedia (produk elektronik: laptop,
# handphone, TV, PC, dll.) yang sudah dibersihkan oleh
# helper/build_elektronik_dataset.py dan tersimpan di
# helper/data/tokopedia_elektronik.csv.
#
#   - Kategori  = kategori toko, dipetakan dari breadcrumb kategori asli Tokopedia
#   - Harga     = harga jual Tokopedia saat scrape (kolom `price`)
#   - Gambar    = foto produk Tokopedia yang sudah diunduh ke frontend
#                 public/products/elektronik/<id>.jpg (kolom `image_url`)
#
# Jalankan: python -m helper.seed

import csv
import os
import random

from app import app
from extensions import db
from models import User, Category, Product


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PRODUCTS_CSV = os.path.join(DATA_DIR, "tokopedia_elektronik.csv")

# ---------------------------------------------------------------------------
# Kategori toko (lihat CATEGORY_RULES di helper/build_elektronik_dataset.py).
# Nama harus persis sama dengan kolom `category` di CSV.
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"name": "Laptop", "description": "Laptop dan notebook untuk kerja dan kuliah"},
    {"name": "Laptop Gaming", "description": "Laptop gaming dengan GPU NVIDIA RTX"},
    {"name": "Handphone", "description": "Smartphone Android dan iOS"},
    {"name": "Tablet", "description": "Tablet Android dan HarmonyOS"},
    {"name": "Televisi", "description": "Smart TV LED, QLED, dan 4K"},
    {"name": "PC & Komputer", "description": "PC desktop, All-in-One, dan PC rakitan"},
    {"name": "Monitor", "description": "Monitor LED dan monitor gaming"},
    {"name": "Headphone & Audio", "description": "Headphone, headset gaming, dan earphone"},
    {"name": "Smartwatch", "description": "Smartwatch dan smartband"},
]
CATEGORY_NAMES = {c["name"] for c in CATEGORIES}


def build_description(row: dict) -> str:
    """Buat deskripsi singkat dari metadata toko hasil scrape."""
    shop = row.get("shop_name", "").strip()
    city = row.get("shop_city", "").strip()
    rating = row.get("rating", "").strip()

    parts = [f"{row['category']} dari Tokopedia."]
    if shop:
        lokasi = f" ({city})" if city else ""
        parts.append(f"Dijual oleh {shop}{lokasi}.")
    if rating:
        parts.append(f"Rating produk {rating}.")
    return " ".join(parts)


def load_products_from_csv():
    """Baca produk hasil scrape dari CSV dan siapkan untuk di-seed."""
    products = []
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            price_raw = (row.get("price") or "").strip()
            category = (row.get("category") or "").strip()
            if not name or not price_raw:
                continue
            try:
                price = float(price_raw)
            except ValueError:
                continue
            if category not in CATEGORY_NAMES:
                raise ValueError(f"Kategori '{category}' untuk '{name[:40]}' tidak ada di CATEGORIES")

            products.append({
                "name": name,
                "price": price,
                "category": category,
                "description": build_description(row),
                # stok acak tapi deterministik agar hasil seed konsisten
                "stock_quantity": random.randint(5, 80),
                "image_url": (row.get("image_url") or "").strip() or None,
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

    category_map = {c.name: c.id for c in Category.query.all()}

    created = updated = skipped = 0
    for data in products:
        category_id = category_map.get(data['category'])
        if not category_id:
            print(f"  ! Category '{data['category']}' not found, skipping '{data['name'][:40]}...'")
            continue

        existing = Product.query.filter_by(name=data['name']).first()
        if existing:
            # Selaraskan harga, kategori, dan gambar dengan data scrape terbaru.
            # Stok dan deskripsi tidak disentuh agar perubahan admin tetap ada.
            changed = False
            if float(existing.price) != data['price']:
                existing.price = data['price']
                changed = True
            if existing.category_id != category_id:
                existing.category_id = category_id
                changed = True
            if data['image_url'] and existing.image_url != data['image_url']:
                existing.image_url = data['image_url']
                changed = True
            updated += changed
            skipped += not changed
            continue

        db.session.add(Product(
            name=data['name'],
            price=data['price'],
            category_id=category_id,
            description=data['description'],
            stock_quantity=data['stock_quantity'],
            image_url=data['image_url'],
        ))
        created += 1

    db.session.commit()
    print(f"  + {created} products created, {updated} updated, {skipped} unchanged")


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
