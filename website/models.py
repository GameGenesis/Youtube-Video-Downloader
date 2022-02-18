from email.policy import default
from time import timezone
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(150))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    urls = db.relationship("Video")