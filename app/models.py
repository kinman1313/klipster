from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Clip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clip_path = db.Column(db.String(300), nullable=False)
    transcription = db.Column(db.Text, nullable=True)
    subtitle_color = db.Column(db.String(20), nullable=True)
    emojis = db.Column(db.String(100), nullable=True)
    effects = db.Column(db.String(100), nullable=True)
    user = db.relationship('User', backref=db.backref('clips', lazy=True))
