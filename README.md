# RevoShop Backend API

## Overview

RevoShop adalah REST API backend untuk aplikasi e-commerce sederhana yang dibangun menggunakan Flask dan PostgreSQL. API ini menyediakan fitur manajemen produk, kategori, pesanan, dan pengguna dengan autentikasi berbasis password hashing.

## Features

- **User Registration & Login** — Register user baru dengan password hashing (werkzeug), login dengan verifikasi kredensial
- **Product CRUD** — Create, Read, Update, Delete produk dengan validasi input (nama wajib, harga positif)
- **Category CRUD** — Manajemen kategori produk, GET category menampilkan produk terkait
- **Order CRUD** — Pembuatan pesanan dengan relasi many-to-many ke produk melalui tabel `order_items`
- **Deletion Guard** — DELETE /products/<id> diblokir jika masih ada order aktif yang terkait
- **Data Validation** — Semua endpoint POST/PUT memvalidasi input dan mengembalikan error 400 yang deskriptif
- **Error Handling** — Semua operasi database dibungkus `try/except`, mengembalikan JSON error (bukan HTML) pada kegagalan
- **Many-to-Many Relationship** — Orders dan Products terhubung melalui tabel asosiasi `order_items`

## Technologies Used

| Technology | Purpose |
|-----------|---------|
| Flask | Web framework |
| SQLAlchemy | ORM (Object Relational Mapper) |
| Flask-Migrate | Database migration (Alembic) |
| PostgreSQL | Database |
| pgAdmin | Database management GUI |
| pytest | Unit & endpoint testing |
| Locust | Load/performance testing |
| python-dotenv | Environment variable management |
| gunicorn | Production WSGI server |
| Werkzeug | Password hashing |
| Render | Cloud deployment platform |

## API Endpoints

### User Module
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Register user baru |
| POST | `/auth/login` | Login (email + password) |

### Product Module
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | List semua produk |
| GET | `/products/<id>` | Detail satu produk |
| POST | `/products` | Buat produk baru |
| PUT | `/products/<id>` | Update produk |
| DELETE | `/products/<id>` | Hapus produk (blocked jika ada active orders) |

### Category Module
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories` | List semua kategori |
| GET | `/categories/<id>` | Detail kategori + produk terkait |
| POST | `/categories` | Buat kategori baru |
| PUT | `/categories/<id>` | Update kategori |
| DELETE | `/categories/<id>` | Hapus kategori |

### Order Module
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders` | List orders (filter by user_id) |
| GET | `/orders/<id>` | Detail order + items + product info |
| POST | `/orders` | Buat order baru |
| PUT | `/orders/<id>` | Update status/total order |
| DELETE | `/orders/<id>` | Hapus order |

## How to Run Locally

### 1. Clone repository
```bash
git clone https://github.com/Revou-FSSE-Jun26/module-2-Sann02.git
cd revoshop-backend
```

### 2. Buat virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment variables
```bash
# Copy .env.example ke .env dan isi dengan nilai yang benar
cp .env.example .env
# Edit .env — isi DATABASE_URL dengan koneksi PostgreSQL kamu
```

### 5. Buat database dan jalankan migrasi
```bash
# Buat database di PostgreSQL (via psql atau pgAdmin)
# Kemudian jalankan migrasi:
flask db upgrade
```

### 6. (Optional) Seed data
```bash
# Cara 1 — via Python seed scripts (direkomendasikan)
python -m helper.seed          # users, categories, products
python -m helper.seed_order    # orders + order_items

# Cara 2 — via file SQL (dokumentasi Checkpoint 1)
psql -U postgres -d revoushop_db -f sql/seed.sql
```

### 7. Jalankan server
```bash
flask run
```
Server berjalan di `http://localhost:5000`

## Testing

### Unit/Endpoint Tests
```bash
pytest tests/ -v
```

### Load Testing (Locust)
```bash
# Pastikan Flask server berjalan di terminal lain
locust --host http://localhost:5000
# Buka http://localhost:8089, set users: 50-200, spawn rate: 10
```

## Project Structure
```
revoshop-backend/
├── run.py              # Entry point (python run.py / gunicorn run:app)
├── app.py              # Flask app initialization
├── config.py           # Configuration (reads from .env)
├── extensions.py       # SQLAlchemy & Migrate instances
├── models.py           # Database models (User, Product, Category, Order)
├── routes.py           # All API endpoints (models / routes / config separated)
├── locustfile.py       # Load testing configuration
├── Procfile            # Deployment (gunicorn)
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not committed)
├── .env.example        # Template for .env
├── .gitignore          # Files excluded from git (.env, venv, __pycache__)
├── helper/             # Database seeding scripts
│   ├── seed.py         # Seed users, categories, products
│   └── seed_order.py   # Seed orders + order_items
├── sql/                # SQL documentation (Checkpoint 1)
│   ├── schema.sql      # Database DDL
│   ├── seed.sql        # Sample data
│   └── queries.sql     # Example SQL queries
├── migrations/         # Alembic / Flask-Migrate migration files
├── screenshots/        # Postman, DBeaver/pgAdmin, and Locust evidence
└── tests/
    ├── conftest.py         # pytest fixtures (in-memory SQLite)
    ├── test_categories.py  # Category CRUD tests (happy + error paths)
    └── test_products.py    # Product CRUD + validation tests
```

## Screenshots

Bukti pengujian tersimpan di folder [`screenshots/`](screenshots/):

- **Postman** — request untuk setiap HTTP method (GET, POST, PUT, DELETE) di seluruh modul, termasuk deletion guard (409) untuk product & category
- **DBeaver / pgAdmin** — tampilan tabel lokal (`users`, `products`, `categories`, `orders`, `order_items`) beserta relasi/foreign key
- **Locust** — dashboard load test dari 50 hingga 200 virtual users

## Deployment

API di-deploy menggunakan Render dengan managed PostgreSQL database.

**Live URL:** *(akan diisi setelah deploy)*

## Author

Sann02 — RevoU FSSE Shanghai Module 2
