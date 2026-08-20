# helper/seed.py
# Script untuk seed data Users, Categories, dan Products
# Jalankan: python -m helper.seed

from app import app
from extensions import db
from models import User, Category, Product


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
    categories = [
        {"name": "Elektronik", "description": "Barang elektronik dan gadget"},
        {"name": "Pakaian", "description": "Pakaian pria dan wanita"},
        {"name": "Makanan", "description": "Makanan dan minuman"},
        {"name": "Buku", "description": "Buku dan alat tulis"},
    ]

    for data in categories:
        existing = Category.query.filter_by(name=data['name']).first()
        if not existing:
            category = Category(name=data['name'], description=data['description'])
            db.session.add(category)
            print(f"  + Category '{data['name']}' created")
        else:
            print(f"  - Category '{data['name']}' already exists, skipped")

    db.session.commit()


def seed_products():
    """Seed data produk"""
    products = [
        {"name": "Laptop Asus ROG", "price": 15000000, "category": "Elektronik", "description": "Laptop gaming high-end", "stock_quantity": 10},
        {"name": "Mouse Logitech G502", "price": 850000, "category": "Elektronik", "description": "Mouse gaming wireless", "stock_quantity": 50},
        {"name": "Keyboard Mechanical", "price": 1200000, "category": "Elektronik", "description": "Keyboard RGB switch blue", "stock_quantity": 30},
        {"name": "Kemeja Flannel", "price": 200000, "category": "Pakaian", "description": "Kemeja bahan tebal", "stock_quantity": 25},
        {"name": "Celana Jeans", "price": 350000, "category": "Pakaian", "description": "Celana jeans slim fit", "stock_quantity": 40},
        {"name": "Indomie Goreng", "price": 3500, "category": "Makanan", "description": "Mie instan rasa original", "stock_quantity": 200},
        {"name": "Kopi Kapal Api", "price": 12000, "category": "Makanan", "description": "Kopi bubuk sachet", "stock_quantity": 150},
        {"name": "Buku Python Programming", "price": 120000, "category": "Buku", "description": "Buku belajar Python", "stock_quantity": 20},
    ]

    for data in products:
        existing = Product.query.filter_by(name=data['name']).first()
        if not existing:
            # Cari category_id berdasarkan nama
            category = Category.query.filter_by(name=data['category']).first()
            if not category:
                print(f"  ! Category '{data['category']}' not found, skipping product '{data['name']}'")
                continue

            product = Product(
                name=data['name'],
                price=data['price'],
                category_id=category.id,
                description=data['description'],
                stock_quantity=data['stock_quantity']
            )
            db.session.add(product)
            print(f"  + Product '{data['name']}' created")
        else:
            print(f"  - Product '{data['name']}' already exists, skipped")

    db.session.commit()


def run():
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
