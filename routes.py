# routes.py
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import User

bp = Blueprint('routes', __name__)

# --- WARM-UP: HARDCODED PRODUCTS ROUTE (Sesuai Syarat Checkpoint 2) ---

HARDCODED_PRODUCTS = [
    {"id": 1, "name": "Laptop Core i7", "price": 15000000},
    {"id": 2, "name": "Mouse Wireless", "price": 250000},
    {"id": 3, "name": "Buku Algoritma", "price": 95000}
]

@bp.route('/products', methods=['GET'])
def get_hardcoded_products():
    return jsonify(HARDCODED_PRODUCTS), 200

@bp.route('/products/<int:product_id>', methods=['GET'])
def get_hardcoded_product(product_id):
    product = next((p for p in HARDCODED_PRODUCTS if p["id"] == product_id), None)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


# --- DATABASE-BACKED ROUTES: USERS ---

@bp.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()

    required_fields = ['username', 'email', 'password_hash']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash']
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already registered"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200