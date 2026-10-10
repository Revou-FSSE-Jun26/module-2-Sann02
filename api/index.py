# api/index.py — entrypoint untuk Vercel Python runtime.
#
# Vercel menjalankan Flask sebagai serverless function. Runtime akan mencari
# variabel WSGI callable bernama `app` di file ini. Kita import objek `app`
# dari app.py di root repo.
#
# Root repo ditambahkan ke sys.path supaya import absolut (app, routes,
# models, config, extensions, dst.) tetap bekerja saat file ini dijalankan
# dari dalam folder api/.
import os
import sys

# Tambahkan root project (satu level di atas folder api/) ke sys.path.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app  # noqa: E402  (import setelah manipulasi sys.path)

# Vercel membutuhkan callable WSGI bernama `app` (sudah tersedia dari import).
