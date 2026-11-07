from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

friends = db.Table(
    "friends",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("friend_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    packs_left = db.Column(db.Integer, default=2)
    last_update = db.Column(db.Float, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    friends = db.relationship(
        "User",
        secondary="friends",
        primaryjoin=(friends.c.user_id == id),
        secondaryjoin=(friends.c.friend_id == id),
        backref=db.backref("friend_of", lazy="dynamic"),
        lazy="dynamic",
    )
    cards = db.relationship("Card", secondary="user_card", back_populates="owners")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_friend_with(self, other):
        return self.friends.filter_by(id=other.id).first() is not None
