# config.py
import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url):
    if not url:
        return url

    # Render kadang memberi URL berawalan "postgres://" (format lama).
    # SQLAlchemy 2.x butuh "postgresql://", jadi kita samakan di sini.
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    # Supabase punya dua pooler:
    #   - port 5432 = session pooler (pool kecil, ~15 koneksi)
    #   - port 6543 = transaction pooler (untuk koneksi singkat / serverless)
    # Backend ini jalan serverless di Vercel, jadi port 5432 cepat penuh dan
    # bikin "max clients reached" -> HTTP 500. Naikkan otomatis ke 6543 supaya
    # benar tanpa bergantung pada env di dashboard.
    if 'pooler.supabase.com:5432' in url:
        url = url.replace('pooler.supabase.com:5432', 'pooler.supabase.com:6543')

    return url


class Config:
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.getenv('DATABASE_URL'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Opsi engine ramah-serverless: buang koneksi mati sebelum dipakai, dan
    # daur ulang koneksi yang sudah lama menganggur supaya tidak memegang slot
    # pooler Supabase lebih lama dari perlu.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

    # JWT: kalau JWT_SECRET_KEY tidak diset, jatuh ke SECRET_KEY supaya app tetap jalan.
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or SECRET_KEY

    # Parse aman: apa pun nilai env-nya, jangan sampai bikin app crash saat boot.
    try:
        JWT_EXPIRES_HOURS = int(os.getenv('JWT_EXPIRES_HOURS', '24'))
    except (TypeError, ValueError):
        JWT_EXPIRES_HOURS = 24

    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
