from app.extensions import db
from app.models import FriendRequest, User


class FriendError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _find_user(username: str | None) -> User:
    user = User.query.filter_by(username=(username or "").strip()).first()
    if not user:
        raise FriendError("Joueur introuvable.", 404)
    return user


def send_request(current: User, username: str) -> str:
    target = _find_user(username)
    if target.id == current.id:
        raise FriendError("Tu ne peux pas t'ajouter toi-même.")
    if current.is_friend_with(target):
        raise FriendError(f"{target.username} est déjà dans tes amis.")

    existing = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current.id) & (FriendRequest.receiver_id == target.id))
        | ((FriendRequest.sender_id == target.id) & (FriendRequest.receiver_id == current.id))
    ).first()
    if existing:
        raise FriendError("Une demande est déjà en cours.")

    db.session.add(FriendRequest(sender_id=current.id, receiver_id=target.id))
    db.session.commit()
    return f"Invitation envoyée à {target.username}."


def _get_received_request(current: User, request_id: int) -> FriendRequest:
    friend_request = db.session.get(FriendRequest, request_id)
    if not friend_request:
        raise FriendError("Invitation introuvable.", 404)
    if friend_request.receiver_id != current.id:
        raise FriendError("Cette invitation ne t'est pas destinée.", 403)
    return friend_request


def accept_request(current: User, request_id: int) -> str:
    friend_request = _get_received_request(current, request_id)
    sender = db.session.get(User, friend_request.sender_id)
    if not sender:
        db.session.delete(friend_request)
        db.session.commit()
        raise FriendError("Cet utilisateur n'existe plus.", 404)

    if not current.is_friend_with(sender):
        current.friends.append(sender)
    if not sender.is_friend_with(current):
        sender.friends.append(current)
    db.session.delete(friend_request)
    db.session.commit()
    return f"{sender.username} est maintenant ton ami."


def reject_request(current: User, request_id: int) -> str:
    friend_request = _get_received_request(current, request_id)
    db.session.delete(friend_request)
    db.session.commit()
    return "Invitation refusée."


def remove_friend(current: User, username: str) -> str:
    friend = _find_user(username)
    if current.is_friend_with(friend):
        current.friends.remove(friend)
    if friend.is_friend_with(current):
        friend.friends.remove(current)
    db.session.commit()
    return f"{friend.username} a été retiré de tes amis."


def suggestions_for(user: User) -> list[User]:
    excluded = {user.id}
    excluded.update(friend.id for friend in user.friends)
    excluded.update(req.receiver_id for req in user.sent_requests)
    excluded.update(req.sender_id for req in user.received_requests)
    return User.query.filter(User.id.notin_(excluded)).order_by(User.username).all()
