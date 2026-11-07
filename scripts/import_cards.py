"""Importe un fichier collection.json dans la base et affiche un résumé.

Usage : python -m scripts.import_cards [chemin/vers/collection.json]
"""
import json
import sys
from pathlib import Path

from sqlalchemy import func

from app import create_app
from app.extensions import db
from app.models import Card

DEFAULT_JSON_PATH = Path("collection.json")


def load_cards(json_path: Path) -> list[dict]:
    if not json_path.exists():
        raise SystemExit(f"❌ Fichier introuvable : '{json_path}'.")
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ JSON invalide : {exc}")


def import_cards(cards_data: list[dict]) -> tuple[int, int]:
    added = skipped = 0
    for data in cards_data:
        if db.session.get(Card, data.get("id")):
            skipped += 1
            continue
        power = data.get("power")
        db.session.add(
            Card(
                id=data.get("id"),
                name=data.get("name"),
                role=data.get("role"),
                description=data.get("description"),
                rarity=data.get("rarity"),
                initials=data.get("initials"),
                power=None if power is None else str(power),
                photo=data.get("photo"),
            )
        )
        added += 1
    db.session.commit()
    return added, skipped


def print_summary() -> None:
    print("📊 ANALYSE DE LA BASE (table 'Card')")
    print("-" * 50)
    print(f"• Total de cartes : {Card.query.count()}")

    print("\n• Répartition par rareté :")
    rows = db.session.query(Card.rarity, func.count(Card.id)).group_by(Card.rarity).all()
    for rarity, count in rows or []:
        print(f"  - {rarity or 'Sans rareté'} : {count} cartes")
    if not rows:
        print("  - Aucune statistique disponible.")

    print("\n• Aperçu de 3 cartes :")
    for card in Card.query.limit(3).all():
        print(f"  [{card.rarity}] {card.name} - Rôle : {card.role or 'Aucun'}")


def main() -> None:
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON_PATH
    cards_data = load_cards(json_path)
    print(f"📦 {len(cards_data)} cartes trouvées dans '{json_path}'.")

    with create_app().app_context():
        added, skipped = import_cards(cards_data)
        print(f"✅ Import terminé : {added} ajoutées, {skipped} déjà existantes.")
        print("-" * 50)
        print_summary()


if __name__ == "__main__":
    main()
