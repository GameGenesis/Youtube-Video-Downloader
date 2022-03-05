from flask_login import UserMixin
from sqlalchemy.sql import func
from . import db

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    url = db.Column(db.String(150))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    link_type = db.Column(db.String(10)) # video or playlist
    file_type = db.Column(db.String(4)) # mp3 or mp4
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # links to distinct user key in the database

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    videos = db.relationship("Video")