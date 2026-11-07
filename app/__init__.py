import secrets
from pathlib import Path

from flask import Flask, g, request, session

from app.extensions import db
from app.services.auth import get_user
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

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    _register_hooks(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    with app.app_context():
        db.create_all()

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

    @app.context_processor
    def inject_user():
        user = g.get("user")
        return {"current_user": user, "is_admin": bool(user and user.is_admin)}


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(413)
    def file_too_large(_error):
        return "Fichier trop volumineux (8 Mo maximum).", 413
