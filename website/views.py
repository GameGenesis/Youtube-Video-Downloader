from flask import Blueprint, render_template, request, flash, send_file
from flask_login import login_required, current_user
from .models import Video
from . import db

from pytube import YouTube
from pathlib import Path
import os

views = Blueprint("views", __name__)

def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(percentage_of_completion)

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

            yt.register_on_progress_callback(on_progress)
            print(f"Fetching \"{video.title}\"..")
            print(f"Fetching successful\n")
            print(f"Information: \n"
            f"File size: {round(video.filesize * 0.000001, 2)} mb\n"
            f"Highest Resolution: {video.resolution}\n"
            f"Author: {yt.author}")
            print("Views: {:,}\n".format(yt.views))

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
                file_path = file_path.replace("mp4", "mp3")
        except Exception:
            flash("Video could not be converted to an MP3 format successfully. File cannot be found or already exists.", category="error")
            return render_template("home.html", user=current_user)

        if current_user.is_authenticated:
            new_video = Video(title=yt.title, url=url, date=date, file_type=file_type, user_id=current_user.id)
            db.session.add(new_video)
            db.session.commit()
        
        flash("Video converted successfully!", category="success")
        print(file_path)
        return send_file(path_or_file=file_path, as_attachment=True)
    return render_template("home.html", user=current_user)

@views.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        try:
            db.session.query(Video).delete()
            db.session.commit()
            flash("Cleared History", category="success")
        except Exception:
            db.session.rollback()
            flash("Could not clear history.", category="error")
    return render_template("history.html", user=current_user)