# app.py
from flask import Flask
from flasgger import Swagger
from extensions import db, migrate
from config import Config

app = Flask(__name__)

# Memuat konfigurasi dari file config.py (yang membaca .env)
app.config.from_object(Config)

# Inisialisasi ekstensi
db.init_app(app)
migrate.init_app(app, db)

# ---- Swagger / OpenAPI (Flasgger) ----
# Template mendefinisikan info API + skema keamanan Bearer (JWT) sehingga
# tombol "Authorize" muncul di Swagger UI (/apidocs).
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "RevoShop API",
        "description": (
            "REST API e-commerce RevoShop: manajemen users, products, "
            "categories, dan orders. Autentikasi JWT bersifat opsional — "
            "endpoint order menerima Bearer token ATAU user_id di body/param."
        ),
        "version": "1.0.0",
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": (
                "JWT access token. Format: **Bearer &lt;token&gt;**. "
                "Dapatkan token dari POST /auth/login."
            ),
        }
    },
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

Swagger(app, template=swagger_template, config=swagger_config)

# Registrasi Blueprint (routes)
from routes import bp
app.register_blueprint(bp)

if __name__ == '__main__':
        app.run(debug=app.config["DEBUG"])
