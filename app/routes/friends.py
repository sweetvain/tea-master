from flask import Blueprint, g, jsonify

from app.services import friends as friend_service
from app.utils.decorators import api_login_required

bp = Blueprint("friends", __name__)


def _respond(action, *args):
    try:
        message = action(g.user, *args)
    except friend_service.FriendError as exc:
        return jsonify({"success": False, "error": exc.message}), exc.status
    return jsonify({"success": True, "message": message})


@bp.route("/send_friend_request/<string:friend_username>", methods=["POST"])
@api_login_required
def send_friend_request(friend_username):
    return _respond(friend_service.send_request, friend_username)


@bp.route("/accept_friend_request/<int:request_id>", methods=["POST"])
@api_login_required
def accept_friend_request(request_id):
    return _respond(friend_service.accept_request, request_id)


@bp.route("/reject_friend_request/<int:request_id>", methods=["POST"])
@api_login_required
def reject_friend_request(request_id):
    return _respond(friend_service.reject_request, request_id)


@bp.route("/remove_friend/<string:friend_username>", methods=["POST"])
@api_login_required
def remove_friend(friend_username):
    return _respond(friend_service.remove_friend, friend_username)
