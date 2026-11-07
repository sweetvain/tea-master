import unicodedata
import uuid

from app.extensions import db
from app.models import Card
from app.services import uploads

RARITIES = {
    "hess": "Hess",
    "rare": "Rare",
    "epique": "Epique",
    "legendaire": "Legendaire",
    "mythique": "Mythique",
    "goat": "GOAT",
}

TEXT_LIMITS = {"name": 100, "role": 100, "initials": 10, "power": 50}
EDITABLE_FIELDS = ("name", "role", "description", "rarity", "initials", "power")


class CardValidationError(ValueError):
    """Données de carte invalides."""


def rarity_key(value: str | None) -> str:
    """'Épique ' -> 'epique' : clé de comparaison sans accent ni casse."""
    text = unicodedata.normalize("NFKD", value or "")
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


def canonical_rarity(value: str | None) -> str | None:
    return RARITIES.get(rarity_key(value))


def rarity_stats(cards) -> dict:
    stats = {"total": 0, **{key: 0 for key in RARITIES}}
    for card in cards:
        stats["total"] += 1
        key = rarity_key(card.rarity)
        if key in RARITIES:
            stats[key] += 1
    return stats


def _clean(value) -> str | None:
    value = (value or "").strip()
    return value or None


def _read_fields(form, only_present: bool) -> dict:
    fields = {}
    for key in EDITABLE_FIELDS:
        if only_present and key not in form:
            continue
        value = _clean(form.get(key))
        if value is not None and len(value) > TEXT_LIMITS.get(key, 10_000):
            raise CardValidationError(f"Le champ « {key} » est trop long.")
        fields[key] = value

    if "rarity" in fields:
        rarity = canonical_rarity(fields["rarity"])
        if rarity is None:
            raise CardValidationError(
                "Rareté invalide (" + ", ".join(RARITIES.values()) + ")."
            )
        fields["rarity"] = rarity

    power = fields.get("power")
    if power is not None and not power.lstrip("-").isdigit():
        raise CardValidationError("La puissance doit être un nombre.")

    if "name" in fields and not fields["name"]:
        raise CardValidationError("Le nom de la carte est obligatoire.")

    return fields


def create_card(form, photo_file=None) -> Card:
    fields = _read_fields(form, only_present=False)
    card = Card(id=str(uuid.uuid4()), photo=uploads.save_photo(photo_file), **fields)
    db.session.add(card)
    db.session.commit()
    return card


def update_card(card: Card, form, photo_file=None) -> Card:
    for key, value in _read_fields(form, only_present=True).items():
        setattr(card, key, value)

    new_photo = uploads.save_photo(photo_file)
    if new_photo:
        old_photo = card.photo
        card.photo = new_photo
        db.session.flush()
        _delete_photo_if_orphan(old_photo)

    db.session.commit()
    return card


def delete_card(card: Card) -> None:
    photo = card.photo
    db.session.delete(card)
    db.session.flush()
    _delete_photo_if_orphan(photo)
    db.session.commit()


def _delete_photo_if_orphan(filename: str | None) -> None:
    if filename and not Card.query.filter_by(photo=filename).first():
        uploads.delete_photo(filename)
