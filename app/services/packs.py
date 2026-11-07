import math
import time

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.models import Card, User


class PackError(Exception):
    """Impossible d'ouvrir un paquet."""


class NoPacksLeft(PackError):
    pass


class AllCardsCollected(PackError):
    pass


def initial_pack_state(now: float | None = None) -> dict:
    return {
        "packs_left": current_app.config["PACKS_PER_REFRESH"],
        "last_update": time.time() if now is None else now,
    }


def refresh_packs(user: User, now: float | None = None) -> bool:
    """Redonne les paquets quand le délai est écoulé. Retourne True si un refresh a eu lieu."""
    now = time.time() if now is None else now
    cooldown = current_app.config["PACK_COOLDOWN_SECONDS"]

    if user.last_update and now - user.last_update >= cooldown:
        user.packs_left = current_app.config["PACKS_PER_REFRESH"]
        user.last_update = now
        db.session.commit()
        return True
    return False


def seconds_until_refresh(user: User, now: float | None = None) -> int | None:
    """Secondes avant le prochain refresh, ou None si aucun timer n'est lancé."""
    if not user.last_update:
        return None
    now = time.time() if now is None else now
    remaining = user.last_update + current_app.config["PACK_COOLDOWN_SECONDS"] - now
    return max(0, math.ceil(remaining))


def open_pack(user: User) -> list[Card]:
    refresh_packs(user)

    if (user.packs_left or 0) <= 0:
        raise NoPacksLeft()

    drawn = (
        Card.query.filter(~Card.owners.any(User.id == user.id))
        .order_by(func.random())
        .limit(current_app.config["CARDS_PER_PACK"])
        .all()
    )
    if not drawn:
        raise AllCardsCollected()

    user.cards.extend(drawn)
    user.packs_left -= 1
    if user.packs_left == 0 and not user.last_update:
        user.last_update = time.time()
    db.session.commit()
    return drawn
