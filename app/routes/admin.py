from flask import Blueprint, abort, current_app, g, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Card, User
from app.services import auth as auth_service
from app.services import cards as card_service
from app.services.uploads import UploadError
from app.utils.decorators import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _back_to_panel():
    return redirect(url_for("admin.panel"))


@bp.route("")
@admin_required
def panel():
    return render_template(
        "admin.html",
        users=User.query.order_by(User.username).all(),
        cards=Card.query.order_by(Card.name).all(),
        protected_username=current_app.config["PROTECTED_ADMIN_USERNAME"],
    )


@bp.route("/toggle-admin/<int:user_id>", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    user = db.get_or_404(User, user_id)
    user.is_admin = True if auth_service.is_protected(user) else not user.is_admin
    db.session.commit()
    return _back_to_panel()


@bp.route("/delete-user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    if not auth_service.is_protected(user) and user.id != g.user.id:
        db.session.delete(user)
        db.session.commit()
    return _back_to_panel()


@bp.route("/add-card", methods=["POST"])
@admin_required
def add_card():
    try:
        card_service.create_card(request.form, request.files.get("photo"))
    except (card_service.CardValidationError, UploadError) as exc:
        abort(400, description=str(exc))
    return _back_to_panel()


@bp.route("/edit-card/<string:card_id>", methods=["GET", "POST"])
@admin_required
def edit_card(card_id):
    card = db.get_or_404(Card, card_id)
    if request.method == "POST":
        try:
            card_service.update_card(card, request.form, request.files.get("photo"))
        except (card_service.CardValidationError, UploadError) as exc:
            abort(400, description=str(exc))
        return _back_to_panel()
    return render_template("edit_card.html", card=card)


@bp.route("/delete-card/<string:card_id>", methods=["POST"])
@admin_required
def delete_card(card_id):
    card_service.delete_card(db.get_or_404(Card, card_id))
    return _back_to_panel()
