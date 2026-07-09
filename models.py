from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

friends = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    packs_left = db.Column(db.Integer, default=2)
    friends = db.relationship('User', secondary='friends', primaryjoin=(friends.c.user_id == id), secondaryjoin=(friends.c.friend_id == id), backref=db.backref('friend_of', lazy='dynamic'), lazy='dynamic')
    last_update = db.Column(db.Float, nullable=True)
    cards = db.relationship('Card', secondary='user_card', back_populates='owners')
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Card(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    description = db.Column(db.Text)
    rarity = db.Column(db.String(50))
    initials = db.Column(db.String(10))
    power = db.Column(db.String(50))
    photo = db.Column(db.String(200))
    owners = db.relationship('User', secondary='user_card', back_populates='cards')

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

user_card = db.Table('user_card',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('card_id', db.String(36), db.ForeignKey('card.id'), primary_key=True)
)

# --- NOUVEAU MODÈLE POUR LES DEMANDES EN ATTENTE ---
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relations pour récupérer facilement l'objet User complet
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')