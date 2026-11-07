import io

from app.extensions import db
from app.models import Card, FriendRequest, User
from app.services import cards as card_service

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def _card_form(**overrides):
    form = {"name": "Veldra", "rarity": "epique", "role": "King", "initials": "VE", "power": "95"}
    form.update(overrides)
    return form


def test_rarity_helpers():
    assert card_service.canonical_rarity("Épique ") == "Epique"
    assert card_service.canonical_rarity("goat") == "GOAT"
    assert card_service.canonical_rarity("inconnue") is None


def test_create_card_endpoint(app, client, make_user, login):
    make_user()
    login()
    data = {**_card_form(), "photo": (io.BytesIO(PNG), "pic.png")}
    response = client.post("/create", data=data, content_type="multipart/form-data")
    assert response.get_json()["success"] is True

    with app.app_context():
        card = Card.query.one()
        assert card.rarity == "Epique"
        assert card.photo.endswith(".png")


def test_create_card_rejects_bad_input(client, make_user, login):
    make_user()
    login()
    bad_rarity = client.post("/create", data=_card_form(rarity="nope"))
    assert bad_rarity.status_code == 400
    bad_ext = client.post(
        "/create",
        data={**_card_form(), "photo": (io.BytesIO(b"<?php"), "shell.php")},
        content_type="multipart/form-data",
    )
    assert bad_ext.status_code == 400
    bad_power = client.post("/create", data=_card_form(power="abc"))
    assert bad_power.status_code == 400


def test_create_requires_login_returns_401_for_ajax(client):
    response = client.post("/create", data=_card_form(), headers={"X-Requested-With": "XMLHttpRequest"})
    assert response.status_code == 401


def test_admin_area_is_protected(client, make_user, login):
    make_user("alice")
    assert client.get("/admin").status_code == 302
    login("alice")
    assert client.get("/admin").status_code == 403
    assert client.post("/admin/delete-card/anything").status_code == 403


def test_edit_card_keeps_fields_missing_from_form(app, client, make_user, login):
    make_user("root", admin=True)
    login("root")
    with app.app_context():
        card = card_service.create_card(_card_form())
        card_id = card.id

    response = client.post(
        f"/admin/edit-card/{card_id}",
        data={"name": "Renamed", "rarity": "GOAT", "description": "desc"},
    )
    assert response.status_code == 302

    with app.app_context():
        card = db.session.get(Card, card_id)
        assert (card.name, card.rarity) == ("Renamed", "GOAT")
        assert (card.role, card.initials, card.power) == ("King", "VE", "95")


def test_admin_can_delete_user_with_pending_requests(app, client, make_user, login):
    make_user("root", admin=True)
    bob_id = make_user("bob")
    carol_id = make_user("carol")
    with app.app_context():
        db.session.add(FriendRequest(sender_id=bob_id, receiver_id=carol_id))
        db.session.commit()

    login("root")
    assert client.post(f"/admin/delete-user/{bob_id}").status_code == 302
    with app.app_context():
        assert db.session.get(User, bob_id) is None
        assert FriendRequest.query.count() == 0


def test_protected_admin_cannot_be_deleted_or_demoted(app, client, make_user, login):
    make_user("root", admin=True)
    vain_id = make_user("vain", admin=True)
    login("root")

    client.post(f"/admin/toggle-admin/{vain_id}")
    client.post(f"/admin/delete-user/{vain_id}")
    with app.app_context():
        user = db.session.get(User, vain_id)
        assert user is not None and user.is_admin


def test_delete_card_removes_unused_photo(app, client, make_user, login):
    make_user("root", admin=True)
    login("root")
    with app.app_context():
        from pathlib import Path

        card = card_service.create_card(
            _card_form(), type("F", (), {"filename": "a.png", "save": lambda self, p: Path(p).write_bytes(PNG)})()
        )
        card_id, photo = card.id, card.photo
        assert (Path(app.config["UPLOAD_FOLDER"]) / photo).exists()

    client.post(f"/admin/delete-card/{card_id}")
    with app.app_context():
        assert db.session.get(Card, card_id) is None
        assert not (Path(app.config["UPLOAD_FOLDER"]) / photo).exists()
