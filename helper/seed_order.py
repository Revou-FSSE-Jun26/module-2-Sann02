# helper/seed_order.py
# Script untuk seed data Orders dan Order Items
# Jalankan: python -m helper.seed_order

from app import app
from extensions import db
from models import User, Product, Order, order_items


def seed_orders():
    """Seed data order beserta order items (many-to-many)"""
    orders_data = [
        {
            "user_id": 1,
            "status": "completed",
            "items": [
                {"product_id": 1, "quantity": 1},  # Laptop Asus ROG
                {"product_id": 2, "quantity": 2},  # Mouse Logitech x2
            ]
        },
        {
            "user_id": 1,
            "status": "pending",
            "items": [
                {"product_id": 3, "quantity": 1},  # Keyboard Mechanical
            ]
        },
        {
            "user_id": 2,
            "status": "completed",
            "items": [
                {"product_id": 4, "quantity": 2},  # Kemeja Flannel x2
                {"product_id": 5, "quantity": 1},  # Celana Jeans
            ]
        },
        {
            "user_id": 3,
            "status": "pending",
            "items": [
                {"product_id": 6, "quantity": 5},  # Indomie x5
                {"product_id": 7, "quantity": 3},  # Kopi x3
                {"product_id": 8, "quantity": 1},  # Buku Python
            ]
        },
    ]

    for order_data in orders_data:
        # Hitung total
        total_amount = 0
        items_to_insert = []

        for item in order_data['items']:
            product = Product.query.get(item['product_id'])
            if product:
                price = float(product.price)
                total_amount += price * item['quantity']
                items_to_insert.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price_at_purchase': price
                })

        # Buat order
        order = Order(
            user_id=order_data['user_id'],
            status=order_data['status'],
            total_amount=total_amount
        )
        db.session.add(order)
        db.session.flush()

        # Insert order items
        for item in items_to_insert:
            db.session.execute(order_items.insert().values(
                order_id=order.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price_at_purchase=item['price_at_purchase']
            ))

        print(f"  + Order #{order.id} (user_id={order_data['user_id']}, status={order_data['status']}, total={total_amount})")

    db.session.commit()


def run():
    with app.app_context():
        print("\n=== Seeding Orders ===\n")

        # Cek apakah sudah ada orders
        existing = Order.query.count()
        if existing > 0:
            print(f"  - {existing} orders already exist. Skipping.")
            print("    (Delete existing orders first if you want to re-seed)")
        else:
            seed_orders()

        print("\n=== Order Seeding Complete ===\n")


if __name__ == '__main__':
    run()
