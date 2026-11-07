import time

from app.extensions import db
from app.models import User
from app.services import packs


def test_pull_gives_new_cards_and_consumes_a_pack(app, client, make_user, make_cards, login):
    make_user()
    make_cards(5)
    login()

    response = client.post("/pull")
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="alice").one()
        assert len(user.cards) == 3
        assert user.packs_left == 1


def test_pull_never_returns_owned_cards(app, client, make_user, make_cards, login):
    make_user()
    make_cards(4)
    login()
    client.post("/pull")
    client.post("/pull")

    with app.app_context():
        user = User.query.filter_by(username="alice").one()
        assert len(user.cards) == 4
        assert len({card.id for card in user.cards}) == 4

    response = client.post("/pull")
    assert response.status_code == 302


def test_pull_without_packs_redirects(app, client, make_user, make_cards, login):
    make_user(packs=0)
    make_cards(5)
    login()

    assert client.post("/pull").status_code == 302
    with app.app_context():
        assert len(User.query.filter_by(username="alice").one().cards) == 0


def test_refresh_after_cooldown(app, make_user):
    user_id = make_user(packs=0)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.last_update = time.time() - 1000
        assert packs.refresh_packs(user) is True
        assert user.packs_left == app.config["PACKS_PER_REFRESH"]


def test_no_refresh_before_cooldown(app, make_user):
    user_id = make_user(packs=0)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.last_update = time.time()
        assert packs.refresh_packs(user) is False
        assert user.packs_left == 0
        assert 0 < packs.seconds_until_refresh(user) <= app.config["PACK_COOLDOWN_SECONDS"]


def test_no_timer_when_never_started(app, make_user):
    user_id = make_user()
    with app.app_context():
        assert packs.seconds_until_refresh(db.session.get(User, user_id)) is None
