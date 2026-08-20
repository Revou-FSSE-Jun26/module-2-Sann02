# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
