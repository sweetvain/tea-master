import pytest

from app.extensions import db
from app.models import FriendRequest, User


@pytest.fixture
def two_users(make_user):
    make_user("alice")
    make_user("bob")


def _client_for(app, username):
    client = app.test_client()
    client.post("/login", data={"username": username, "password": "secret123"})
    return client


def test_friend_api_requires_login(client):
    response = client.post("/send_friend_request/bob")
    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_full_friend_flow(app, two_users):
    alice, bob = _client_for(app, "alice"), _client_for(app, "bob")

    sent = alice.post("/send_friend_request/bob")
    assert sent.get_json()["success"] is True
    assert sent.get_json()["message"]
    assert alice.post("/send_friend_request/bob").status_code == 400

    with app.app_context():
        request_id = FriendRequest.query.one().id

    assert bob.post(f"/accept_friend_request/{request_id}").get_json()["success"] is True
    with app.app_context():
        a, b = (User.query.filter_by(username=n).one() for n in ("alice", "bob"))
        assert a.is_friend_with(b) and b.is_friend_with(a)

    assert alice.post("/send_friend_request/bob").status_code == 400
    assert alice.post("/remove_friend/bob").get_json()["success"] is True
    with app.app_context():
        a, b = (User.query.filter_by(username=n).one() for n in ("alice", "bob"))
        assert not a.is_friend_with(b) and not b.is_friend_with(a)


def test_cannot_add_yourself_or_unknown_user(app, two_users):
    alice = _client_for(app, "alice")
    assert alice.post("/send_friend_request/alice").status_code == 400
    assert alice.post("/send_friend_request/ghost").status_code == 404


def test_only_receiver_can_answer_a_request(app, two_users, make_user):
    make_user("mallory")
    alice, mallory = _client_for(app, "alice"), _client_for(app, "mallory")
    alice.post("/send_friend_request/bob")
    with app.app_context():
        request_id = FriendRequest.query.one().id

    assert mallory.post(f"/reject_friend_request/{request_id}").status_code == 403
    assert mallory.post(f"/accept_friend_request/{request_id}").status_code == 403
    with app.app_context():
        assert FriendRequest.query.count() == 1


def test_profile_lists_suggestions(app, two_users):
    alice = _client_for(app, "alice")
    html = alice.get("/profile").get_data(as_text=True)
    assert 'data-username="bob"' in html

    alice.post("/send_friend_request/bob")
    assert 'data-username="bob"' not in alice.get("/profile").get_data(as_text=True)
