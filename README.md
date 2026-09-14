# RevoShop Backend API

**Live API:** https://web-production-1b0825.up.railway.app
Contoh: [`/products`](https://web-production-1b0825.up.railway.app/products)

## Overview

RevoShop adalah REST API backend untuk aplikasi e-commerce sederhana yang dibangun menggunakan Flask dan PostgreSQL. API ini menyediakan fitur manajemen produk, kategori, pesanan, dan pengguna dengan autentikasi berbasis password hashing serta JWT (JSON Web Token) untuk pengelolaan sesi login. Aplikasi berjalan live di Railway dengan managed PostgreSQL.

## Features

- **User Registration & Login** — Register user baru dengan password hashing (werkzeug), login dengan verifikasi kredensial
- **JWT Authentication** — Login mengembalikan JWT `access_token`. Endpoint order dapat mengambil identitas user dari token (`Authorization: Bearer <token>`), dengan fallback ke `user_id` agar tetap kompatibel
- **Product CRUD** — Create, Read, Update, Delete produk dengan validasi input (nama wajib, harga positif)
- **Category CRUD** — Manajemen kategori produk, GET category menampilkan produk terkait
- **Order CRUD** — Pembuatan pesanan dengan relasi many-to-many ke produk melalui tabel `order_items`
- **Deletion Guard** — DELETE /products/<id> diblokir jika masih ada order aktif yang terkait
- **Data Validation** — Semua endpoint POST/PUT memvalidasi input dan mengembalikan error 400 yang deskriptif
- **Error Handling** — Semua operasi database dibungkus `try/except`, mengembalikan JSON error (bukan HTML) pada kegagalan
- **Many-to-Many Relationship** — Orders dan Products terhubung melalui tabel asosiasi `order_items`
- **Swagger / OpenAPI Docs** — Dokumentasi API interaktif (Flasgger) di `/apidocs/`, lengkap dengan tombol Authorize untuk uji endpoint ber-JWT
- **Docker** — `Dockerfile` + `docker-compose.yml` untuk menjalankan API bersama PostgreSQL dalam container

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
| PyJWT | JSON Web Token (generate & verify access token) |
| Flasgger | Swagger / OpenAPI interactive docs |
| Docker & Docker Compose | Containerization (API + PostgreSQL) |
| Railway | Cloud deployment platform (API + PostgreSQL) |

## API Endpoints

### User Module
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Register user baru |
| POST | `/auth/login` | Login (email + password), mengembalikan JWT `access_token` |

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

## Authentication (JWT)

> **Catatan:** Module 2 tidak mewajibkan autentikasi berbasis token — mengirim `user_id` di body/param sudah cukup. JWT di sini bersifat **opsional/eksploratif** dan diimplementasikan secara **non-destruktif**: endpoint lama tetap berjalan dengan pola `user_id`.

**Cara kerja:**

1. **Login** untuk mendapatkan token:
   ```bash
   POST /auth/login
   Content-Type: application/json

   { "email": "budi@test.com", "password": "pass123" }
   ```
   Respons:
   ```json
   {
     "user": { "id": 1, "username": "budi", "email": "budi@test.com", "role": "user" },
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "Bearer"
   }
   ```

2. **Gunakan token** pada request order dengan header:
   ```
   Authorization: Bearer <access_token>
   ```
   Saat token dikirim, `user_id` diambil otomatis dari token (tidak perlu dikirim di body):
   ```bash
   POST /orders
   Authorization: Bearer eyJhbGciOiJIUzI1Ni...
   Content-Type: application/json

   { "items": [ { "product_id": 1, "quantity": 2 } ] }
   ```

3. **Tanpa token** — endpoint tetap menerima `user_id` di body/param seperti biasa (fallback), sehingga kompatibel dengan grader, pytest, dan Locust.

**Perilaku token:** token invalid atau kedaluwarsa dibalas `401`. Masa berlaku diatur lewat `JWT_EXPIRES_HOURS` (default 24 jam).

## API Documentation (Swagger)

Dokumentasi API interaktif dibuat otomatis dengan **Flasgger** (Swagger UI). Setelah server berjalan, buka:

```
http://localhost:5000/apidocs/
```

- Semua endpoint dikelompokkan per tag: **Users, Auth, Products, Categories, Orders**.
- Spec OpenAPI mentah tersedia di `http://localhost:5000/apispec.json`.
- Untuk menguji endpoint order yang memakai JWT:
  1. Jalankan `POST /auth/login`, salin `access_token` dari respons.
  2. Klik tombol **Authorize** di kanan atas Swagger UI.
  3. Masukkan `Bearer <access_token>`, lalu klik Authorize.
  4. Sekarang tombol **Try it out** pada endpoint order akan menyertakan token tersebut.

Dokumentasi tiap endpoint ditulis sebagai docstring YAML di dalam `routes.py`, jadi dokumentasi selalu menyatu dengan kode.

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
# Edit .env — isi:
#   DATABASE_URL   -> koneksi PostgreSQL kamu
#   SECRET_KEY     -> secret key aplikasi
#   JWT_SECRET_KEY -> secret untuk sign/verify JWT (isi nilai acak yang kuat)
```

> **Catatan keamanan:** nilai rahasia asli (termasuk `JWT_SECRET_KEY`) hanya ada di `.env` yang **tidak di-commit** (sudah di `.gitignore`). File `.env.example` hanya berisi placeholder. Untuk menghasilkan secret acak yang kuat:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> Jika `JWT_SECRET_KEY` tidak diisi, aplikasi otomatis fallback ke `SECRET_KEY` agar tetap berjalan.

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

## Running with Docker

Proyek ini menyertakan `Dockerfile` dan `docker-compose.yml` untuk menjalankan API bersama PostgreSQL tanpa perlu setup manual.

### Jalankan semua (API + DB)
```bash
# Build image dan jalankan container
docker compose up --build

# Di terminal lain — apply migrasi ke DB di dalam container
docker compose exec api flask db upgrade

# (Opsional) seed data
docker compose exec api python -m helper.seed
docker compose exec api python -m helper.seed_order
```

Setelah jalan:
- API — `http://localhost:5000`
- Swagger UI — `http://localhost:5000/apidocs/`
- PostgreSQL — `localhost:5432` (user: `postgres`, pass: `postgres`, db: `revoushop_db`)

### Menghentikan
```bash
docker compose down       # stop container (data DB tetap tersimpan di volume)
docker compose down -v    # stop + hapus volume (reset database)
```

### Build image saja (tanpa compose)
```bash
docker build -t revoshop-api .
docker run -p 5000:5000 --env-file .env revoshop-api
```

> **Catatan:** secret (`SECRET_KEY`, `JWT_SECRET_KEY`) diambil dari environment. Pada `docker-compose.yml` nilainya dibaca dari shell/`.env` dengan fallback nilai dev; ganti dengan nilai kuat untuk produksi.

## Project Structure
```
revoshop-backend/
├── run.py              # Entry point (python run.py / gunicorn run:app)
├── app.py              # Flask app initialization
├── config.py           # Configuration (reads from .env)
├── extensions.py       # SQLAlchemy & Migrate instances
├── models.py           # Database models (User, Product, Category, Order)
├── routes.py           # All API endpoints (models / routes / config separated)
├── auth_jwt.py         # JWT helper (generate/verify token, resolve_user_id)
├── locustfile.py       # Load testing configuration
├── Procfile            # Deployment (gunicorn)
├── Dockerfile          # Container image (Flask + gunicorn)
├── docker-compose.yml  # API + PostgreSQL untuk lokal
├── .dockerignore       # File yang dikecualikan dari build context
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
- **Hosted database (Railway)** — tampilan tabel yang sama pada database produksi Railway
- **Live API (Postman)** — request CRUD terhadap URL produksi Railway
- **Locust** — dashboard load test dari 50 hingga 200 virtual users

## Deployment

API di-deploy menggunakan **Railway** dengan managed PostgreSQL database.

**Live URL:** https://web-production-1b0825.up.railway.app

### Deployment setup (Railway)
- **Start command:** `gunicorn run:app --bind 0.0.0.0:$PORT` (via `Procfile`)
- **Environment variables** (di-set pada service Railway):
  - `DATABASE_URL` — direferensikan dari service PostgreSQL: `${{Postgres.DATABASE_URL}}`
  - `SECRET_KEY` — secret key aplikasi
  - `JWT_SECRET_KEY` — secret untuk JWT (set eksplisit di produksi; karena `.env` tidak ikut ter-push)
  - `FLASK_DEBUG` — `False` di produksi
- **Migrasi produksi** dijalankan di dalam jaringan Railway:
  ```bash
  railway ssh --service web "flask db upgrade"
  ```

`config.py` menormalkan awalan `postgres://` menjadi `postgresql://` secara otomatis agar kompatibel dengan SQLAlchemy 2.x.

## Author

Sann02 — RevoU FSSE Shanghai Module 2
