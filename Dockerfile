# Dockerfile — image produksi untuk RevoShop API
FROM python:3.12-slim

# Konfigurasi Python:
#  - PYTHONDONTWRITEBYTECODE: jangan tulis file .pyc
#  - PYTHONUNBUFFERED: log langsung ter-flush (penting untuk container)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

WORKDIR /app

# Catatan: psycopg2-binary sudah menyediakan wheel pra-kompilasi, jadi kita
# TIDAK perlu gcc/libpq-dev. Ini membuat build jauh lebih cepat & image kecil.

# Install dependency Python lebih dulu (memanfaatkan layer cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin sisa kode aplikasi
COPY . .

# Jadikan entrypoint executable
RUN chmod +x entrypoint.sh

# Jalankan migrasi lalu start gunicorn pada $PORT yang disediakan platform.
# entrypoint.sh menangani ekspansi $PORT (Koyeb/Render/Railway) secara aman.
CMD ["./entrypoint.sh"]
