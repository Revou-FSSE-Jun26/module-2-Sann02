# helper/seed.py
# Script untuk seed data Users, Categories, dan Products.
# Data produk diambil dari hasil scraping Tokopedia (kategori Komputer & Laptop)
# yang tersimpan di helper/data/tokopedia_komputer_laptop.csv
#
# Jalankan: python -m helper.seed

import csv
import json
import os
import random

from app import app
from extensions import db
from models import User, Category, Product


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PRODUCTS_CSV = os.path.join(DATA_DIR, "tokopedia_komputer_laptop.csv")
# Peta nama-produk (persis) -> URL foto produk.
# Sumber: Unsplash (images.unsplash.com) - hotlink diizinkan dan URL stabil
# (tanpa signature kedaluwarsa, tidak seperti CDN Tokopedia yang balas 403).
IMAGES_JSON = os.path.join(DATA_DIR, "product_images.json")

# Fallback per-kategori bila sebuah produk tidak ada di peta gambar.
# Urutan penting: pola yang lebih spesifik diletakkan lebih dulu.
# (kata kunci dicek terhadap nama produk yang di-lowercase)
IMAGE_FALLBACK_RULES = [
    (("mousepad", "mouse pad", "deskmat"), "https://images.unsplash.com/photo-1629429407759-01cd3d7cfb38?w=640&q=80"),
    (("keyboard", "combo"), "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=640&q=80"),
    (("mouse",), "https://images.unsplash.com/photo-1527814050087-3793815479db?w=640&q=80"),
    (("joystick", "game pad", "gamepad", "stick"), "https://images.unsplash.com/photo-1592840496694-26d035b52b48?w=640&q=80"),
    (("macbook", "macos"), "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=640&q=80"),
    (("backpack", "ransel", "punggung"), "https://images.unsplash.com/photo-1491637639811-60e2756cc1c7?w=640&q=80"),
    (("tas", "sleeve", "sling", "handbag", "standbag", "selempang", "bag"), "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=640&q=80"),
    (("stand", "holder", "dudukan"), "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=640&q=80"),
    (("ram", "sodimm", "memory"), "https://images.unsplash.com/photo-1562976540-1502c2145186?w=640&q=80"),
    (("cooler", "pendingin", "cooling", "heatpipe", "kipas"), "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=640&q=80"),
    (("wifi", "wireless adapter", "wn722n", "archer"), "https://images.unsplash.com/photo-1606904825846-647eb07f5be2?w=640&q=80"),
    (("charger", "adaptor", "adapter", "gan", "desktop charger"), "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=640&q=80"),
    (("hub", "docking", "splitter", "switch", "converter", "type c"), "https://images.unsplash.com/photo-1625842268584-8f3296236761?w=640&q=80"),
    (("kabel", "cable"), "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=640&q=80"),
    (("laptop", "notebook"), "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=640&q=80"),
]
# Fallback terakhir bila tidak ada kata kunci yang cocok sama sekali.
IMAGE_FALLBACK_DEFAULT = "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=640&q=80"


def load_image_map():
    """Muat peta nama-produk -> URL gambar. Return {} kalau file tidak ada.

    Kunci yang diawali '_' (mis. '_comment') diabaikan supaya bisa menaruh
    catatan di dalam file JSON tanpa ikut terbaca sebagai produk.
    """
    if not os.path.exists(IMAGES_JSON):
        return {}
    with open(IMAGES_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def match_image_url(name: str, image_map: dict):
    """Pilih URL gambar untuk sebuah produk.

    1. Coba kecocokan nama persis dari peta gambar (paling akurat).
    2. Kalau tidak ada, pakai fallback berbasis kata kunci per-kategori
       sehingga produk baru pun tetap dapat gambar yang masuk akal.
    """
    if name in image_map:
        return image_map[name]

    lower = name.lower()
    for keywords, url in IMAGE_FALLBACK_RULES:
        if any(k in lower for k in keywords):
            return url
    return IMAGE_FALLBACK_DEFAULT


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
    image_map = load_image_map()
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
                "image_url": match_image_url(name, image_map),
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
    updated = 0
    for data in products:
        existing = Product.query.filter_by(name=data['name']).first()
        if existing:
            # Produk sudah ada: segarkan image_url bila berbeda dari data terbaru.
            if data.get('image_url') and existing.image_url != data['image_url']:
                existing.image_url = data['image_url']
                updated += 1
            else:
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
            image_url=data.get('image_url'),
        )
        db.session.add(product)
        created += 1

    db.session.commit()
    print(f"  + {created} products created, {updated} image_url updated, {skipped} skipped")


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
