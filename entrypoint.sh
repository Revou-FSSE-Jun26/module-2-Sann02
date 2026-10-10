#!/bin/sh
# entrypoint.sh — dijalankan saat container start.
# 1) Terapkan migrasi database (buat/upgrade tabel) sebelum app melayani request.
# 2) Jalankan gunicorn, bind ke $PORT yang disediakan platform (Koyeb/Render/
#    Railway). Kalau $PORT tidak diset, fallback ke 8000.
set -e

echo "Running database migrations..."
flask db upgrade

PORT="${PORT:-8000}"
echo "Starting gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn run:app --bind "0.0.0.0:${PORT}" --workers 2
