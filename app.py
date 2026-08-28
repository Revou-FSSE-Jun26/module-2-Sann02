# app.py
from flask import Flask
from extensions import db, migrate
from config import Config

app = Flask(__name__)

# Memuat konfigurasi dari file config.py (yang membaca .env)
app.config.from_object(Config)

# Inisialisasi ekstensi
db.init_app(app)
migrate.init_app(app, db)

# Registrasi Blueprint (routes)
from routes import bp
app.register_blueprint(bp)

if __name__ == '__main__':
        app.run(debug=app.config["DEBUG"])