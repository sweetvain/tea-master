import os
import secrets
from functools import lru_cache
from pathlib import Path

from flask import Flask, g, request, session

from app.extensions import db
from app.services.auth import get_user
from app.services.seed import normalize_photo_names, seed_if_empty
from config import BASE_DIR, Config


def create_app(config_object=Config) -> Flask:
    app = Flask(
        __name__,
        instance_path=str(BASE_DIR / "instance"),
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(config_object)

    if not app.config.get("SECRET_KEY"):
        if not (app.debug or app.testing):
            raise RuntimeError("SECRET_KEY manquante : définis-la dans le fichier .env.")
        app.config["SECRET_KEY"] = secrets.token_hex(32)

    if app.config["ON_VERCEL"] and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL manquante : le disque de Vercel est en lecture seule, "
            "SQLite n'y fonctionne pas. Configure une base PostgreSQL."
        )

    for folder in (app.instance_path, app.config["UPLOAD_FOLDER"]):
        try:
            Path(folder).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # disque en lecture seule (hébergement serverless)

    db.init_app(app)
    _register_hooks(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    with app.app_context():
        db.create_all()
        if not app.testing:
            seed_if_empty()
            normalize_photo_names()

    return app


def _register_blueprints(app: Flask) -> None:
    from app.routes import BLUEPRINTS

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


def _register_hooks(app: Flask) -> None:
    @app.before_request
    def load_current_user():
        g.user = None
        if request.endpoint == "static":
            return
        user_id = session.get("user_id")
        if user_id:
            g.user = get_user(user_id)
            if g.user is None:
                session.clear()

    build_id = (os.getenv("VERCEL_GIT_COMMIT_SHA") or "")[:8]

    @app.url_defaults
    def version_static_files(endpoint, values):
        """Ajoute ?v=<build> aux CSS/JS/images du site pour pouvoir les mettre en cache longtemps."""
        filename = values.get("filename", "")
        if endpoint != "static" or "v" in values or filename.startswith("uploads/"):
            return
        values["v"] = build_id or _file_version(app, filename)

    @app.after_request
    def cache_static_files(response):
        if request.endpoint == "static" and response.status_code == 200:
            if request.args.get("v"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.context_processor
    def inject_user():
        user = g.get("user")
        return {"current_user": user, "is_admin": bool(user and user.is_admin)}


@lru_cache(maxsize=512)
def _file_version(app: Flask, filename: str) -> str:
    try:
        return str(int((Path(app.static_folder) / filename).stat().st_mtime))
    except OSError:
        return "0"


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(413)
    def file_too_large(_error):
        return "Fichier trop volumineux (8 Mo maximum).", 413
