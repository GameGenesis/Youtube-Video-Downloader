from flask import Blueprint, render_template, request, flash, send_file
from flask_login import login_required, current_user
from .models import Video
from . import db

from pytube import YouTube
from pathlib import Path
import os

views = Blueprint("views", __name__)

@views.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form.get("url")
        date = request.form.get("date")

        try:
            yt = YouTube(url)
        except Exception:
            flash("Video URL is not valid.", category="error")
            return render_template("home.html", user=current_user)
        
        try:
            if request.form["convert"] == "mp4":
                video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                file_type = "mp4"
            elif request.form["convert"] == "mp3":
                video = yt.streams.filter(only_audio=True).get_audio_only()
                file_type = "mp3"

            print(f"Downloading \"{video.title}\"..")
            downloads_path = str(Path.home() / "Downloads")
            video.download(downloads_path)
        except Exception:
            flash("Video could not be converted.", category="error")
            return render_template("home.html", user=current_user)

        try:
            if file_type == "mp3":
                file_path = os.path.join(downloads_path, video.default_filename)
                os.rename(file_path, file_path.replace("mp4", "mp3"))
        except:
            flash("Video could not be converted to an MP3 format successfully. File cannot be found or already exists.", category="error")
            return render_template("home.html", user=current_user)

        if current_user.is_authenticated:
            new_video = Video(title=yt.title, url=url, date=date, file_type=file_type, user_id=current_user.id)
            db.session.add(new_video)
            db.session.commit()
        
        flash("Video converted successfully!", category="success")
        
    return render_template("home.html", user=current_user)

@views.route("/history", methods=["GET", "POST"])
@login_required
def history():
    return render_template("history.html", user=current_user)