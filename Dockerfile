# Dockerfile — image produksi untuk RevoShop API
FROM python:3.12-slim

# Konfigurasi Python:
#  - PYTHONDONTWRITEBYTECODE: jangan tulis file .pyc
#  - PYTHONUNBUFFERED: log langsung ter-flush (penting untuk container)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

# Catatan: psycopg2-binary sudah menyediakan wheel pra-kompilasi, jadi kita
# TIDAK perlu gcc/libpq-dev. Ini membuat build jauh lebih cepat & image kecil.

# Install dependency Python lebih dulu (memanfaatkan layer cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin sisa kode aplikasi
COPY . .

EXPOSE 5000

# Jalankan lewat gunicorn (WSGI server produksi).
# Pakai bentuk shell agar $PORT dari environment ter-expand.
CMD gunicorn run:app --bind 0.0.0.0:${PORT} --workers 2
