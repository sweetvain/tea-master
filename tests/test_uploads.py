from app.extensions import db
from app.models import Card
from app.services.seed import normalize_photo_names
from app.services.uploads import safe_name

UUID = "2c4737f1-a2be-48b7-afdc-747a7e3ebd0e"


def test_safe_name_strips_accents_and_symbols():
    assert safe_name(f"{UUID}_pablituxrare·_kiffeur_de_rousse.jpg") == f"{UUID}.jpg"
    assert safe_name(f"{UUID}_s’excuser_à_genoux_?.JPG") == f"{UUID}.jpg"


def test_safe_name_keeps_ascii_names_untouched():
    assert safe_name(f"{UUID}_tea.jpg") == f"{UUID}_tea.jpg"
    assert safe_name(f"{UUID}.png") == f"{UUID}.png"


def test_safe_name_without_uuid_is_deterministic():
    assert safe_name("été.png") == safe_name("été.png")
    assert safe_name("été.png").endswith(".png")


def test_normalize_photo_names_updates_cards(app):
    with app.app_context():
        db.session.add_all([
            Card(id="a", name="A", photo=f"{UUID}_é.jpg"),
            Card(id="b", name="B", photo=f"{UUID}_ok.jpg"),
            Card(id="c", name="C", photo=None),
        ])
        db.session.commit()

        assert normalize_photo_names() == 1
        assert db.session.get(Card, "a").photo == f"{UUID}.jpg"
        assert db.session.get(Card, "b").photo == f"{UUID}_ok.jpg"
        assert normalize_photo_names() == 0
