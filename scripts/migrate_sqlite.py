"""Copie les données d'une base SQLite vers la base configurée dans DATABASE_URL.

Usage : python -m scripts.migrate_sqlite instance/teacards.db

Les tables sont créées si besoin. Les lignes déjà présentes (même clé primaire) sont ignorées,
le script peut donc être relancé sans risque.
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, select

from app import create_app
from app.extensions import db

# Ordre important : les tables référencées d'abord.
TABLES = ("user", "card", "user_card", "friends", "friend_request")


def _key(row, primary_key_columns):
    return tuple(row[column.name] for column in primary_key_columns)


def migrate(source_path: Path) -> None:
    if not source_path.exists():
        raise SystemExit(f"❌ Base source introuvable : {source_path}")

    source = create_engine(f"sqlite:///{source_path.resolve().as_posix()}")
    app = create_app()

    with app.app_context():
        for name in TABLES:
            table = db.metadata.tables[name]
            primary_key = list(table.primary_key.columns)

            with source.connect() as src:
                if not source.dialect.has_table(src, name):
                    print(f"- {name}: absente de la source, ignorée")
                    continue
                rows = [dict(r._mapping) for r in src.execute(select(table))]

            existing = {
                _key(r._mapping, primary_key)
                for r in db.session.execute(select(*primary_key))
            }
            new_rows = [r for r in rows if _key(r, primary_key) not in existing]
            if new_rows:
                db.session.execute(table.insert(), new_rows)
            db.session.commit()
            print(f"- {name}: {len(new_rows)} ajoutées, {len(rows) - len(new_rows)} déjà présentes")

        _reset_postgres_sequences()
    print("✅ Migration terminée.")


def _reset_postgres_sequences() -> None:
    """Recale les compteurs auto-incrément PostgreSQL après insertion d'identifiants explicites."""
    if db.engine.dialect.name != "postgresql":
        return
    for name in ("user", "friend_request"):
        db.session.execute(
            db.text(
                f'SELECT setval(pg_get_serial_sequence(\'"{name}"\', \'id\'), '
                f'COALESCE((SELECT MAX(id) FROM "{name}"), 1))'
            )
        )
    db.session.commit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage : python -m scripts.migrate_sqlite chemin/vers/teacards.db")
    migrate(Path(sys.argv[1]))
