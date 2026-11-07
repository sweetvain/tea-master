from flask import Blueprint, current_app, g, jsonify, redirect, render_template, request, url_for

from app.services import cards as card_service
from app.services import packs as pack_service
from app.services.uploads import UploadError
from app.utils.decorators import api_login_required, login_required

bp = Blueprint("main", __name__)


def _pack_state() -> dict:
    return {
        "packs": g.user.packs_left,
        "packs_max": current_app.config["PACKS_PER_REFRESH"],
        "refresh_in": pack_service.seconds_until_refresh(g.user),
    }


def _render_packs(**extra):
    pack_service.refresh_packs(g.user)
    return render_template(
        "index.html",
        **_pack_state(),
        pack_name=current_app.config["PACK_NAME"],
        pack_series=current_app.config["PACK_SERIES"],
        cards_per_pack=current_app.config["CARDS_PER_PACK"],
        message=request.args.get("message"),
        **extra,
    )


@bp.route("/")
@login_required
def index():
    return _render_packs()


@bp.route("/collection")
@login_required
def collection():
    cards = [card.to_dict() for card in g.user.cards]
    return render_template(
        "collection.html",
        collection=cards,
        stats=card_service.rarity_stats(g.user.cards),
    )


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "GET":
        return render_template("create.html")

    try:
        card_service.create_card(request.form, request.files.get("photo"))
    except (card_service.CardValidationError, UploadError) as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True, "message": "Carte créée avec succès !"})


@bp.route("/pull", methods=["POST"])
@login_required
def pull():
    """Ouverture sans JavaScript : la page des paquets s'affiche avec les cartes déjà tirées."""
    try:
        drawn = pack_service.open_pack(g.user)
    except pack_service.AllCardsCollected:
        return redirect(
            url_for("main.index", message="Vous avez collecté toutes les cartes disponibles !")
        )
    except pack_service.NoPacksLeft:
        return redirect(url_for("main.index"))

    return _render_packs(drawn_cards=[card.to_dict() for card in drawn])


@bp.route("/api/pull", methods=["POST"])
@api_login_required
def pull_api():
    """Ouverture d'un paquet depuis l'animation (réponse JSON, pas de rechargement de page)."""
    try:
        drawn = pack_service.open_pack(g.user)
    except pack_service.AllCardsCollected:
        return jsonify(
            {"success": False, "code": "all_collected",
             "error": "Vous avez collecté toutes les cartes disponibles !"}
        ), 409
    except pack_service.NoPacksLeft:
        return jsonify(
            {"success": False, "code": "no_packs", "error": "Plus de paquet disponible pour le moment."}
        ), 409

    return jsonify(
        {
            "success": True,
            "cards": [card.to_dict() for card in drawn],
            "packs_left": g.user.packs_left,
            "refresh_in": pack_service.seconds_until_refresh(g.user),
        }
    )
