from flask import Blueprint, g, render_template

from app.models import User
from app.services import cards as card_service
from app.services import friends as friend_service
from app.utils.decorators import login_required

bp = Blueprint("profile", __name__)


@bp.route("/profile")
@login_required
def profile():
    return render_template(
        "profile.html",
        user=g.user,
        friends=g.user.friends.order_by(User.username).all(),
        friend_suggestions=friend_service.suggestions_for(g.user),
        pending_requests=g.user.received_requests,
        stats=card_service.rarity_stats(g.user.cards),
    )
