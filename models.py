# models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# Association Table untuk Many-to-Many (Orders <-> Products)
order_items = db.Table('order_items',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), nullable=False),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), nullable=False),
    db.Column('quantity', db.Integer, nullable=False),
    db.Column('price_at_purchase', db.Numeric(10, 2), nullable=False)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), server_default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke Order
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Relasi ke Product
    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    def to_dict_with_products(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "products": [p.to_dict() for p in self.products]
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock_quantity": self.stock_quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi Many-to-Many ke Product melalui order_items
    products = db.relationship('Product', secondary=order_items, lazy='subquery',
        backref=db.backref('orders', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def to_dict_with_items(self):
        """Return order dengan detail order_items dan produk"""
        items = db.session.execute(
            order_items.select().where(order_items.c.order_id == self.id)
        ).fetchall()

        items_list = []
        for item in items:
            product = Product.query.get(item.product_id)
            items_list.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if product else None,
                "quantity": item.quantity,
                "price_at_purchase": float(item.price_at_purchase)
            })

        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": items_list
        }
