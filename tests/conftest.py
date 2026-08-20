# tests/conftest.py
import pytest
import os

# Override DATABASE_URL sebelum app di-import
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app as flask_app
from extensions import db


@pytest.fixture(scope='function')
def app():
    """Create application for testing with in-memory SQLite."""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
