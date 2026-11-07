import uuid

import pytest

from app import create_app
from app.extensions import db
from app.models import Card, User
from config import TestingConfig


@pytest.fixture
def app(tmp_path):
    class Config(TestingConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    app = create_app(Config)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make(username="alice", password="secret123", admin=False, packs=2):
        with app.app_context():
            user = User(username=username, packs_left=packs, is_admin=admin)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user.id

    return _make


@pytest.fixture
def make_cards(app):
    def _make(count=5, rarity="Rare"):
        with app.app_context():
            for i in range(count):
                db.session.add(Card(id=str(uuid.uuid4()), name=f"Carte {i}", rarity=rarity))
            db.session.commit()

    return _make


@pytest.fixture
def login(client):
    def _login(username="alice", password="secret123"):
        return client.post("/login", data={"username": username, "password": password})

    return _login
