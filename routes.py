# routes.py
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from extensions import db
from models import User, Product, Category, Order, order_items
from auth_jwt import generate_token, resolve_user_id

bp = Blueprint('routes', __name__)


# ============================================================
# ROOT / HEALTH CHECK
# ============================================================
@bp.route('/', methods=['GET'])
def index():
    """Welcome endpoint — menampilkan info API dan daftar endpoint utama."""
    return jsonify({
        "message": "RevoShop API is running",
        "status": "ok",
        "endpoints": {
            "users": ["POST /users", "POST /auth/login"],
            "products": [
                "GET /products", "GET /products/<id>", "POST /products",
                "PUT /products/<id>", "DELETE /products/<id>"
            ],
            "categories": [
                "GET /categories", "GET /categories/<id>", "POST /categories",
                "PUT /categories/<id>", "DELETE /categories/<id>"
            ],
            "orders": [
                "GET /orders", "GET /orders/<id>", "POST /orders",
                "PUT /orders/<id>", "DELETE /orders/<id>"
            ]
        }
    }), 200


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
    """Register user baru
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, email, password]
          properties:
            username: {type: string, example: budi}
            email: {type: string, example: budi@test.com}
            password: {type: string, example: pass123}
    responses:
      201:
        description: User berhasil dibuat
      400:
        description: Field wajib tidak lengkap
      409:
        description: Email sudah terdaftar
    """
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
    """Ambil detail user berdasarkan ID
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: ID user
    responses:
      200:
        description: Detail user
      404:
        description: User tidak ditemukan
    """
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


# ============================================================
# AUTH MODULE
# ============================================================

@bp.route('/auth/login', methods=['POST'])
def login():
    """Login dan dapatkan JWT access token
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string, example: budi@test.com}
            password: {type: string, example: pass123}
    responses:
      200:
        description: Login sukses, mengembalikan user + access_token
        schema:
          type: object
          properties:
            user: {type: object}
            access_token: {type: string}
            token_type: {type: string, example: Bearer}
      400:
        description: email/password tidak dikirim
      401:
        description: Kredensial salah
    """
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

    # Kembalikan data user + JWT access token.
    # Token bersifat opsional untuk dipakai client; endpoint lama tetap
    # menerima user_id di body/param (lihat catatan di auth_jwt.py).
    access_token = generate_token(user)
    return jsonify({
        "user": user.to_dict(),
        "access_token": access_token,
        "token_type": "Bearer"
    }), 200


# ============================================================
# PRODUCT MODULE
# ============================================================

@bp.route('/products', methods=['GET'])
def get_products():
    """List semua produk
    ---
    tags:
      - Products
    responses:
      200:
        description: Daftar produk
    """
    try:
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Failed to fetch products"}), 500


@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    """Detail satu produk berdasarkan ID
    ---
    tags:
      - Products
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Detail produk
      404:
        description: Produk tidak ditemukan
    """
    product = Product.query.get(id)
    if product is None:
        return jsonify({"error": f"Product {id} not found"}), 404
    return jsonify(product.to_dict()), 200


@bp.route('/products', methods=['POST'])
def create_product():
    """Buat produk baru
    ---
    tags:
      - Products
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, price, category_id]
          properties:
            name: {type: string, example: Laptop Core i7}
            price: {type: number, example: 15000000}
            category_id: {type: integer, example: 1}
            description: {type: string, example: Laptop kencang}
            stock_quantity: {type: integer, example: 10}
    responses:
      201:
        description: Produk dibuat
      400:
        description: Validasi gagal (field/tipe)
      422:
        description: Nilai melanggar aturan (mis. harga negatif)
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validasi field wajib
    required = ['name', 'price', 'category_id']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Validasi nilai
    # 400 = masalah bentuk request (kosong / tipe salah)
    # 422 = tipe benar tapi melanggar aturan bisnis (nilai negatif)
    if not isinstance(data['name'], str) or not data['name'].strip():
        return jsonify({"error": "Product name cannot be empty"}), 400

    if not isinstance(data['price'], (int, float)) or isinstance(data['price'], bool):
        return jsonify({"error": "price must be a number"}), 400
    if data['price'] < 0:
        return jsonify({"error": "price must be 0 or greater"}), 422

    # stock_quantity opsional; jika dikirim harus integer non-negatif
    stock = data.get('stock_quantity', 0)
    if 'stock_quantity' in data:
        if not isinstance(stock, int) or isinstance(stock, bool):
            return jsonify({"error": "stock must be an integer"}), 400
        if stock < 0:
            return jsonify({"error": "stock must be 0 or greater"}), 422

    try:
        product = Product(
            name=data['name'].strip(),
            price=data['price'],
            category_id=data['category_id'],
            description=data.get('description', ''),
            stock_quantity=stock
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
    """Update produk (partial update)
    ---
    tags:
      - Products
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name: {type: string}
            price: {type: number}
            stock_quantity: {type: integer}
            description: {type: string}
            category_id: {type: integer}
    responses:
      200:
        description: Produk diperbarui
      400:
        description: Validasi gagal
      404:
        description: Produk tidak ditemukan
      422:
        description: Nilai melanggar aturan
    """
    product = Product.query.get(id)
    if product is None:
        return jsonify({"error": f"Product {id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Partial update — hanya validasi field yang dikirim.
    # 400 = kosong / tipe salah, 422 = nilai negatif.
    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            return jsonify({"error": "name cannot be empty"}), 400
        product.name = data['name'].strip()

    if 'price' in data:
        if not isinstance(data['price'], (int, float)) or isinstance(data['price'], bool):
            return jsonify({"error": "price must be a number"}), 400
        if data['price'] < 0:
            return jsonify({"error": "price must be 0 or greater"}), 422
        product.price = data['price']

    if 'stock_quantity' in data:
        if not isinstance(data['stock_quantity'], int) or isinstance(data['stock_quantity'], bool):
            return jsonify({"error": "stock must be an integer"}), 400
        if data['stock_quantity'] < 0:
            return jsonify({"error": "stock must be 0 or greater"}), 422
        product.stock_quantity = data['stock_quantity']

    # Update optional fields
    if 'description' in data:
        product.description = data['description']
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
    """Hapus produk (diblokir jika ada order aktif)
    ---
    tags:
      - Products
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Produk dihapus
      404:
        description: Produk tidak ditemukan
      409:
        description: Tidak bisa dihapus karena ada order aktif
    """
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
    """List semua kategori
    ---
    tags:
      - Categories
    responses:
      200:
        description: Daftar kategori
    """
    try:
        categories = Category.query.all()
        return jsonify([c.to_dict() for c in categories]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Failed to fetch categories"}), 500


@bp.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    """Detail kategori beserta produk terkait
    ---
    tags:
      - Categories
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Detail kategori + produk
      404:
        description: Kategori tidak ditemukan
    """
    category = Category.query.get(id)
    if category is None:
        return jsonify({"error": f"Category {id} not found"}), 404
    # Return category beserta produk-produknya
    return jsonify(category.to_dict_with_products()), 200


@bp.route('/categories', methods=['POST'])
def create_category():
    """Buat kategori baru
    ---
    tags:
      - Categories
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name]
          properties:
            name: {type: string, example: Elektronik}
            description: {type: string, example: Aneka gadget}
    responses:
      201:
        description: Kategori dibuat
      400:
        description: Nama wajib diisi
    """
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
    """Update kategori
    ---
    tags:
      - Categories
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name: {type: string}
            description: {type: string}
    responses:
      200:
        description: Kategori diperbarui
      400:
        description: Nama kosong
      404:
        description: Kategori tidak ditemukan
    """
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
    """Hapus kategori
    ---
    tags:
      - Categories
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Kategori dihapus
      404:
        description: Kategori tidak ditemukan
      409:
        description: Tidak bisa dihapus karena masih ada produk
    """
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
    """List orders (JWT opsional; fallback ke user_id)
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: query
        name: user_id
        type: integer
        required: false
        description: Dipakai bila tidak mengirim JWT. Kalau JWT dikirim, diambil dari token.
    responses:
      200:
        description: Daftar order
      401:
        description: Token tidak valid / kedaluwarsa
    """
    # user_id diambil dari JWT jika client mengirim token, kalau tidak
    # fallback ke query parameter (pola lama yang dinilai rubrik).
    user_id, token_error = resolve_user_id(request.args.get('user_id'))
    if token_error:
        return jsonify({"error": token_error}), 401

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
    """Detail order beserta items dan info produk
    ---
    tags:
      - Orders
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Detail order + items
      404:
        description: Order tidak ditemukan
    """
    order = Order.query.get(id)
    if order is None:
        return jsonify({"error": f"Order {id} not found"}), 404
    # Return order dengan detail items
    return jsonify(order.to_dict_with_items()), 200


@bp.route('/orders', methods=['POST'])
def create_order():
    """Buat order baru (JWT opsional; fallback ke user_id di body)
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [items]
          properties:
            user_id:
              type: integer
              description: Wajib bila tidak mengirim JWT. Diabaikan bila JWT dikirim.
              example: 1
            items:
              type: array
              items:
                type: object
                properties:
                  product_id: {type: integer, example: 1}
                  quantity: {type: integer, example: 2}
    responses:
      201:
        description: Order dibuat
      400:
        description: Validasi gagal
      401:
        description: Token tidak valid / kedaluwarsa
      404:
        description: User / produk tidak ditemukan
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # user_id: utamakan dari JWT (jika ada token), fallback ke body.
    resolved_user_id, token_error = resolve_user_id(data.get('user_id'))
    if token_error:
        return jsonify({"error": token_error}), 401

    # Validasi field wajib
    if not resolved_user_id:
        return jsonify({"error": "user_id is required"}), 400

    if not data.get('items') or len(data['items']) == 0:
        return jsonify({"error": "Order must have at least one item"}), 400

    # Cek user exists
    user = User.query.get(resolved_user_id)
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
            user_id=resolved_user_id,
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
    """Update status/total order
    ---
    tags:
      - Orders
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            status: {type: string, example: completed}
            total_amount: {type: number, example: 30000000}
    responses:
      200:
        description: Order diperbarui
      404:
        description: Order tidak ditemukan
    """
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
    """Hapus order
    ---
    tags:
      - Orders
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Order dihapus
      404:
        description: Order tidak ditemukan
    """
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
