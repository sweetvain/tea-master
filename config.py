import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///teacards.db")
    # Heroku/Neon/Supabase fournissent parfois "postgres://", que SQLAlchemy n'accepte plus.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ON_VERCEL = bool(os.getenv("VERCEL"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    ALLOWED_IMAGE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "gif", "webp"})
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    PACK_COOLDOWN_SECONDS = _int_env("PACK_COOLDOWN_SECONDS", 10)
    PACKS_PER_REFRESH = 2
    CARDS_PER_PACK = 3

    # Personnalisation du paquet affiché sur la page d'accueil
    PACK_NAME = os.getenv("PACK_NAME", "TeaMasters")
    PACK_SERIES = os.getenv("PACK_SERIES", "Série 1")

    PROTECTED_ADMIN_USERNAME = os.getenv("PROTECTED_ADMIN_USERNAME", "vain")

    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 30
    MIN_PASSWORD_LENGTH = 6


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    PACK_COOLDOWN_SECONDS = 60
