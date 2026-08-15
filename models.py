# models.py
from datetime import datetime
from extensions import db

# Association Table untuk Many-to-Many (Orders <-> Products)
# Rubrik Checkpoint 2 mewajibkan order_items dibuat menggunakan db.Table()
order_items = db.Table('order_items',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), nullable=False),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), nullable=False),
    db.Column('quantity', db.Integer, nullable=False),
    db.Column('price_at_purchase', db.Numeric(10, 2), nullable=False)
)

class User(db.Model):
    __tablename__ = 'users'

    # Sesuai instruksi CP2: id, username, email, password_hash, created_at
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- UPDATE CHECKPOINT 2: Penambahan kolom role ---
    role = db.Column(db.String(50), server_default='user')
    
    # Relasi ke Order (Satu user bisa punya banyak order)
    orders = db.relationship('Order', backref='user', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,  # Menampilkan role saat request GET
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relasi ke Product
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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