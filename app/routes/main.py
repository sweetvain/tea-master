from flask import Blueprint, current_app, g, jsonify, redirect, render_template, request, url_for

from app.services import cards as card_service
from app.services import packs as pack_service
from app.services.uploads import UploadError
from app.utils.decorators import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    pack_service.refresh_packs(g.user)
    return render_template(
        "index.html",
        packs=g.user.packs_left,
        packs_max=current_app.config["PACKS_PER_REFRESH"],
        refresh_in=pack_service.seconds_until_refresh(g.user),
        message=request.args.get("message"),
    )


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
    try:
        drawn = pack_service.open_pack(g.user)
    except pack_service.AllCardsCollected:
        return redirect(
            url_for("main.index", message="Vous avez collecté toutes les cartes disponibles !")
        )
    except pack_service.NoPacksLeft:
        return redirect(url_for("main.index"))

    return render_template("pull.html", drawn_cards=[card.to_dict() for card in drawn])
