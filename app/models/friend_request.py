from app.extensions import db


class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        backref=db.backref("sent_requests", cascade="all, delete-orphan"),
    )
    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        backref=db.backref("received_requests", cascade="all, delete-orphan"),
    )
