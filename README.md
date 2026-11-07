# TeaMasters

Jeu de cartes à collectionner entre potes : ouvre des paquets, complète ta collection, ajoute des amis et crée tes propres cartes.

Stack : Flask, Flask-SQLAlchemy (SQLite par défaut), GSAP côté front.

## Lancer le projet

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # puis renseigne SECRET_KEY
python run.py                   # ou : flask --app app run
```

Importer des cartes depuis un fichier JSON :

```bash
python -m scripts.import_cards collection.json
```

Lancer les tests :

```bash
pip install -r requirements-dev.txt
pytest
```

## Configuration (`.env`)

| Variable | Rôle | Défaut |
|---|---|---|
| `SECRET_KEY` | Clé de session Flask (**obligatoire** hors debug) | — |
| `DATABASE_URL` | URL SQLAlchemy | `sqlite:///teacards.db` (dans `instance/`) |
| `PACK_COOLDOWN_SECONDS` | Délai de rechargement des paquets | `10` |
| `PROTECTED_ADMIN_USERNAME` | Admin impossible à rétrograder/supprimer | `vain` |
| `FLASK_DEBUG` | `1` pour activer le debug en local | `0` |

## Mise en ligne (Vercel)

Le repo est relié à Vercel (base PostgreSQL Neon) : chaque push sur `main` redéploie le site (`vercel.json` + `api/index.py`).

Vercel est « serverless » : le disque est en lecture seule et ne garde rien entre deux requêtes, donc **SQLite ne peut pas y fonctionner**. Il faut une base PostgreSQL hébergée (Neon, Supabase, Vercel Postgres...).

1. Crée une base PostgreSQL et copie son URL de connexion.
2. Dans Vercel > Settings > Environment Variables, ajoute :
   - `DATABASE_URL` : l'URL PostgreSQL
   - `SECRET_KEY` : une longue valeur aléatoire
3. Copie les données existantes (cartes, comptes) vers la nouvelle base, depuis ta machine :
   ```bash
   set DATABASE_URL=<url postgres>        # Linux/macOS : export DATABASE_URL=...
   set SECRET_KEY=x
   python -m scripts.migrate_sqlite instance/teacards.db
   ```
4. Redéploie (Deployments > Redeploy).

Limites sur Vercel : les images déjà dans `static/uploads` sont servies normalement, mais **l'envoi de nouvelles images est désactivé** (disque en lecture seule). Pour l'activer, il faudra un stockage externe (Vercel Blob, Supabase Storage, S3...).

## Structure

```
config.py              Configuration (Config, TestingConfig)
run.py                 Point d'entrée
app/
  __init__.py          create_app() : factory, hooks, blueprints
  extensions.py        Instance SQLAlchemy
  models/              User, Card, FriendRequest
  services/            Logique métier (sans Flask request/response)
    auth.py              inscription, connexion, validation
    packs.py             cooldown, tirage d'un paquet
    cards.py             validation, création/édition/suppression, stats
    friends.py           demandes d'amis
    uploads.py           sauvegarde sécurisée des images
  routes/              Blueprints (fins : ils appellent les services)
    auth.py main.py profile.py friends.py admin.py
  utils/decorators.py  login_required, api_login_required, admin_required
scripts/import_cards.py  Import JSON -> base
templates/             Pages Jinja (header.html et card_modal.html partagés)
static/css, static/js  Styles et scripts par page / composant
tests/                 Tests pytest
```
