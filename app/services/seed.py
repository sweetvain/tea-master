import json
from pathlib import Path

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Card, User, user_card
from app.services.uploads import safe_name

SEED_FILE = Path(__file__).resolve().parents[2] / "data" / "seed.json"


def seed_if_empty() -> bool:
    """Charge data/seed.json (cartes + comptes initiaux) quand la base est totalement vide."""
    if not SEED_FILE.exists() or User.query.first() or Card.query.first():
        return False

    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    try:
        db.session.add_all(User(**user) for user in data["users"])
        db.session.add_all(Card(**card) for card in data["cards"])
        db.session.flush()
        if data["user_cards"]:
            db.session.execute(user_card.insert(), data["user_cards"])
        db.session.commit()
    except IntegrityError:
        db.session.rollback()  # un autre démarrage simultané a déjà importé les données
        return False

    _reset_postgres_sequence()
    current_app.logger.warning(
        "seed: %d comptes, %d cartes importés", len(data["users"]), len(data["cards"])
    )
    return True


def normalize_photo_names() -> int:
    """Remplace les anciens noms d'images (accents, « ? »...) par leur version ASCII."""
    changed = 0
    for card in Card.query.filter(Card.photo.isnot(None)).all():
        new_name = safe_name(card.photo)
        if new_name != card.photo:
            card.photo = new_name
            changed += 1
    if changed:
        db.session.commit()
    return changed


def _reset_postgres_sequence() -> None:
    if db.engine.dialect.name == "postgresql":
        db.session.execute(
            db.text(
                "SELECT setval(pg_get_serial_sequence('\"user\"', 'id'), "
                "COALESCE((SELECT MAX(id) FROM \"user\"), 1))"
            )
        )
        db.session.commit()
