# config.py
import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url):
    # Render kadang memberi URL berawalan "postgres://" (format lama).
    # SQLAlchemy 2.x butuh "postgresql://", jadi kita samakan di sini.
    if url and url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.getenv('DATABASE_URL'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
