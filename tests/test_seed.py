from app.models import Card, User
from app.services.seed import seed_if_empty


def test_seed_loads_initial_data_once(app):
    with app.app_context():
        assert seed_if_empty() is True
        assert User.query.count() >= 1
        assert Card.query.count() > 0
        owner = User.query.filter_by(is_admin=True).first()
        assert owner is not None and len(owner.cards) > 0

        assert seed_if_empty() is False


def test_seed_skipped_when_database_not_empty(app, make_user):
    make_user("someone")
    with app.app_context():
        assert seed_if_empty() is False
        assert Card.query.count() == 0
