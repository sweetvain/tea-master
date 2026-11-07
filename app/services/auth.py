import re

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.models import User
from app.services import packs

USERNAME_PATTERN = re.compile(r"^[\w.-]+$")
MAX_PASSWORD_LENGTH = 128


class AuthError(ValueError):
    """Erreur d'authentification ou d'inscription, message destiné à l'utilisateur."""


def get_user(user_id) -> User | None:
    return db.session.get(User, user_id) if user_id else None


def authenticate(username: str | None, password: str | None) -> User:
    user = User.query.filter_by(username=(username or "").strip()).first()
    if not user or not user.check_password(password or ""):
        raise AuthError("Pseudo ou code secret incorrect.")
    return user


def register_user(username: str | None, password: str | None) -> User:
    config = current_app.config
    username = (username or "").strip()
    password = password or ""

    min_len, max_len = config["MIN_USERNAME_LENGTH"], config["MAX_USERNAME_LENGTH"]
    if not min_len <= len(username) <= max_len:
        raise AuthError(f"Le pseudo doit faire entre {min_len} et {max_len} caractères.")
    if not USERNAME_PATTERN.match(username):
        raise AuthError("Le pseudo ne peut contenir que des lettres, chiffres, « _ », « . » et « - ».")
    if not config["MIN_PASSWORD_LENGTH"] <= len(password) <= MAX_PASSWORD_LENGTH:
        raise AuthError(
            f"Le code secret doit faire au moins {config['MIN_PASSWORD_LENGTH']} caractères."
        )
    if User.query.filter(func.lower(User.username) == username.lower()).first():
        raise AuthError("Ce pseudo est déjà pris.")

    user = User(username=username, **packs.initial_pack_state())
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def is_protected(user: User) -> bool:
    """L'administrateur historique ne peut être ni rétrogradé ni supprimé."""
    return user.username.lower() == current_app.config["PROTECTED_ADMIN_USERNAME"].lower()
