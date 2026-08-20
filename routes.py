# routes.py
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from extensions import db
from models import User, Product, Category, Order, order_items

bp = Blueprint('routes', __name__)


# ============================================================
# USER MODULE
# ============================================================

# --- CHECKPOINT 2: Hardcoded Products (Warm-up) ---
HARDCODED_PRODUCTS = [
    {"id": 1, "name": "Laptop Core i7", "price": 15000000},
    {"id": 2, "name": "Mouse Wireless", "price": 250000},
    {"id": 3, "name": "Buku Algoritma", "price": 95000}
]

@bp.route('/hardcoded-products', methods=['GET'])
def get_hardcoded_products():
    return jsonify(HARDCODED_PRODUCTS), 200

@bp.route('/hardcoded-products/<int:product_id>', methods=['GET'])
def get_hardcoded_product(product_id):
    product = next((p for p in HARDCODED_PRODUCTS if p["id"] == product_id), None)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@bp.route('/users', methods=['POST'])
@bp.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validasi field wajib
    required = ['username', 'email', 'password']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        new_user = User(
            username=data['username'],
            email=data['email']
        )
        new_user.set_password(data['password'])  # Hash password

        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered"}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


# ============================================================
# AUTH MODULE
# ============================================================

@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    # Same error for missing user AND wrong password (prevent user enumeration)
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify(user.to_dict()), 200


# ============================================================
# PRODUCT MODULE
# ============================================================

@bp.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Failed to fetch products"}), 500


@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({"error": f"Product {id} not found"}), 404
    return jsonify(product.to_dict()), 200


@bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validasi field wajib
    required = ['name', 'price', 'category_id']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Validasi nilai
    if not data['name'].strip():
        return jsonify({"error": "Product name cannot be empty"}), 400

    if not isinstance(data['price'], (int, float)) or data['price'] <= 0:
        return jsonify({"error": "Price must be a positive number"}), 400

    try:
        product = Product(
            name=data['name'].strip(),
            price=data['price'],
            category_id=data['category_id'],
            description=data.get('description', ''),
            stock_quantity=data.get('stock_quantity', 0)
        )
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Invalid category_id"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({"error": f"Product {id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validasi jika name dikirim
    if 'name' in data:
        if not data['name'].strip():
            return jsonify({"error": "Product name cannot be empty"}), 400
        product.name = data['name'].strip()

    # Validasi jika price dikirim
    if 'price' in data:
        if not isinstance(data['price'], (int, float)) or data['price'] <= 0:
            return jsonify({"error": "Price must be a positive number"}), 400
        product.price = data['price']

    # Update optional fields
    if 'description' in data:
        product.description = data['description']
    if 'stock_quantity' in data:
        product.stock_quantity = data['stock_quantity']
    if 'category_id' in data:
        product.category_id = data['category_id']

    try:
        db.session.commit()
        return jsonify(product.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Invalid category_id"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if product is None:
        return jsonify({"error": f"Product {id} not found"}), 404

    # Cek apakah ada active orders yang terkait produk ini
    active_orders = db.session.execute(
        order_items.select().where(order_items.c.product_id == id)
    ).fetchall()

    if active_orders:
        # Cek apakah order-nya masih aktif (bukan completed/cancelled)
        for item in active_orders:
            order = Order.query.get(item.order_id)
            if order and order.status not in ('completed', 'cancelled'):
                return jsonify({
                    "error": "Cannot delete product with active orders"
                }), 409

    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": f"Product {id} deleted successfully"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


# ============================================================
# CATEGORY MODULE
# ============================================================

@bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify([c.to_dict() for c in categories]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Failed to fetch categories"}), 500


@bp.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    category = Category.query.get(id)
    if category is None:
        return jsonify({"error": f"Category {id} not found"}), 404
    # Return category beserta produk-produknya
    return jsonify(category.to_dict_with_products()), 200


@bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    if not data.get('name') or not data['name'].strip():
        return jsonify({"error": "Category name is required"}), 400

    try:
        category = Category(
            name=data['name'].strip(),
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/categories/<int:id>', methods=['PUT'])
def update_category(id):
    category = Category.query.get(id)
    if category is None:
        return jsonify({"error": f"Category {id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    if 'name' in data:
        if not data['name'].strip():
            return jsonify({"error": "Category name cannot be empty"}), 400
        category.name = data['name'].strip()

    if 'description' in data:
        category.description = data['description']

    try:
        db.session.commit()
        return jsonify(category.to_dict()), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    category = Category.query.get(id)
    if category is None:
        return jsonify({"error": f"Category {id} not found"}), 404

    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({"message": f"Category {id} deleted successfully"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Cannot delete category with existing products"}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


# ============================================================
# ORDER MODULE
# ============================================================

@bp.route('/orders', methods=['GET'])
def get_orders():
    # user_id dari query parameter
    user_id = request.args.get('user_id')

    try:
        if user_id:
            orders = Order.query.filter_by(user_id=user_id).all()
        else:
            orders = Order.query.all()
        return jsonify([o.to_dict() for o in orders]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Failed to fetch orders"}), 500


@bp.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get(id)
    if order is None:
        return jsonify({"error": f"Order {id} not found"}), 404
    # Return order dengan detail items
    return jsonify(order.to_dict_with_items()), 200


@bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validasi field wajib
    if not data.get('user_id'):
        return jsonify({"error": "user_id is required"}), 400

    if not data.get('items') or len(data['items']) == 0:
        return jsonify({"error": "Order must have at least one item"}), 400

    # Cek user exists
    user = User.query.get(data['user_id'])
    if user is None:
        return jsonify({"error": "User not found"}), 404

    try:
        # Hitung total dan validasi produk
        total_amount = 0
        items_to_insert = []

        for item in data['items']:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)

            if not product_id:
                return jsonify({"error": "Each item must have a product_id"}), 400

            product = Product.query.get(product_id)
            if product is None:
                return jsonify({"error": f"Product {product_id} not found"}), 404

            price_at_purchase = float(product.price)
            total_amount += price_at_purchase * quantity

            items_to_insert.append({
                'product_id': product_id,
                'quantity': quantity,
                'price_at_purchase': price_at_purchase
            })

        # Buat order
        order = Order(
            user_id=data['user_id'],
            status='pending',
            total_amount=total_amount
        )
        db.session.add(order)
        db.session.flush()  # Dapat order.id tanpa commit

        # Insert order items
        for item in items_to_insert:
            db.session.execute(order_items.insert().values(
                order_id=order.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price_at_purchase=item['price_at_purchase']
            ))

        db.session.commit()
        return jsonify(order.to_dict_with_items()), 201

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    order = Order.query.get(id)
    if order is None:
        return jsonify({"error": f"Order {id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Partial update — only update fields present in body
    if 'status' in data:
        order.status = data['status']
    if 'total_amount' in data:
        order.total_amount = data['total_amount']

    try:
        db.session.commit()
        return jsonify(order.to_dict()), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Order.query.get(id)
    if order is None:
        return jsonify({"error": f"Order {id} not found"}), 404

    try:
        # Clear many-to-many relationship dulu
        order.products = []
        db.session.flush()
        # Hapus order items
        db.session.execute(order_items.delete().where(order_items.c.order_id == id))
        db.session.flush()
        # Hapus order
        db.session.delete(order)
        db.session.commit()
        return jsonify({"message": f"Order {id} deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
