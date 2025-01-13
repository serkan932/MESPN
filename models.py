from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)  # Nouveau champ
    phone_number = db.Column(db.String(20), unique=True, nullable=False)  # Nouveau champ
    password = db.Column(db.String(150), nullable=False)
    profile_picture = db.Column(db.String(200))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_1_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_2_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relations pour accéder aux utilisateurs
    user_1 = db.relationship('User', foreign_keys=[user_1_id])
    user_2 = db.relationship('User', foreign_keys=[user_2_id])

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations pour accéder aux utilisateurs
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations pour accéder aux utilisateurs
    user = db.relationship('User', foreign_keys=[user_id])
    friend = db.relationship('User', foreign_keys=[friend_id])


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=True)  # Message privé
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)  # Message de groupe
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations
    sender = db.relationship('User', foreign_keys=[sender_id])
    conversation = db.relationship('Conversation', foreign_keys=[conversation_id])
    group = db.relationship('Group', foreign_keys=[group_id])


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relation vers l'utilisateur administrateur
    admin = db.relationship('User', foreign_keys=[admin_id])


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
