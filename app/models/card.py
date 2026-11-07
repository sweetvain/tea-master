from app.extensions import db

user_card = db.Table(
    "user_card",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("card_id", db.String(36), db.ForeignKey("card.id"), primary_key=True),
)


class Card(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    description = db.Column(db.Text)
    rarity = db.Column(db.String(50))
    initials = db.Column(db.String(10))
    power = db.Column(db.String(50))
    photo = db.Column(db.String(200))

    owners = db.relationship("User", secondary="user_card", back_populates="cards")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "rarity": self.rarity,
            "initials": self.initials,
            "power": self.power,
            "photo": self.photo,
        }
