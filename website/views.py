from io import BytesIO
import json
from flask import Blueprint, redirect, render_template, request, flash, send_file, url_for, session
from flask_login import login_required, current_user
from .models import Video
from . import db

from pytube import YouTube, Playlist
from youtubesearchpython import VideosSearch, PlaylistsSearch
import os
import zipfile
from shutil import rmtree

views = Blueprint("views", __name__)

#Pages

#Redirects to video conversion page (/video)
@views.route("/")
def home():
    session.clear()
    return redirect(url_for("views.video"))

@views.route("/video", methods=["GET", "POST"])
def video():
    if request.method == "POST":
        url = request.form.get("url")
        date = request.form.get("date")
        
        session.clear()

        try:
            yt = YouTube(url)
        except Exception:
            if "playlist?" in url:
                flash("Playlists can only be converted on the playlist page.", category="error")
            else:
                flash("Video URL is not valid.", category="error")
            return render_template("video.html", user=current_user)
        
        try:
            video, file_type, downloads_path = download_video(yt)
        except Exception:
            flash("Video could not be converted.", category="error")
            return render_template("video.html", user=current_user)

        file_path = os.path.join(downloads_path, video.default_filename)

        try:
            if file_type == "mp3":
                if os.path.exists(file_path.replace("mp4", "mp3")):
                    os.remove(file_path.replace("mp4", "mp3"))
                os.rename(file_path, file_path.replace("mp4", "mp3"))
                file_path = file_path.replace("mp4", "mp3")
        except Exception:
            flash("Video could not be converted to an MP3 format successfully. File cannot be found or already exists.", category="error")
            return render_template("video.html", user=current_user)

        save_history(url, date, video.title, "video", file_type)
        
        try:
            downloaded_file = send_file(path_or_file=file_path, as_attachment=True)
            rmtree(downloads_path)
            return downloaded_file
        except Exception:
           flash("Video converted successfully, but the file couldn't be sent to the browser! Saved to temporary folder.", category="warning")
           print(f"File stored at: {file_path}")

    session["playlist_url"] = ""
    try: url = session["video_url"]
    except Exception: url = ""
    return render_template("video.html", user=current_user, url=url)

@views.route("/playlist", methods=["GET", "POST"])
def playlist():
    if request.method == "POST":
        playlist_url = request.form.get("url")
        date = request.form.get("date")

        session.clear()

        try:
            playlist = Playlist(playlist_url)
        except Exception:
            flash("Playlist URL is not valid.", category="error")
            return render_template("playlist.html", user=current_user)
        
        file_type = "mp4" if request.form["convert"] == "mp4" else "mp3"
        
        try:
            downloads_path = os.path.join(os.getcwd(), "temp")
            playlist_path = os.path.join(downloads_path, playlist.title)

            for index, url in enumerate(playlist):
                yt = YouTube(url)
                if file_type == "mp4":
                    video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    video.download(playlist_path)
                else:
                    video = yt.streams.filter(only_audio=True).get_audio_only()
                    video.download(playlist_path)
                    file_path = os.path.join(playlist_path, video.default_filename)
                    if os.path.exists(file_path.replace("mp4", "mp3")):
                        os.remove(file_path.replace("mp4", "mp3"))
                    os.rename(file_path, file_path.replace("mp4", "mp3"))
                
                try: playlist_len = playlist.length
                except Exception: playlist_len = 1
                
                debug_video_progress(yt, video, file_type, f"({index + 1} of {playlist_len}): ")
        except:
            flash("Playlist could not be converted. Playlist may not exist.", category="error")
            return render_template("playlist.html", user=current_user)
        
        save_history(playlist_url, date, playlist.title, "playlist", file_type)

        try:
            zip_file_name, memory_file = zip_folder(playlist.title, playlist_path)
            downloaded_file = send_file(memory_file, attachment_filename=zip_file_name, as_attachment=True)
            rmtree(downloads_path)
            return downloaded_file
        except Exception:
            flash("Playlist converted successfully, but the zipped folder couldn't be sent to the browser! Saved to temporary folder.", category="warning")
            print(f"Folder stored at: {downloads_path}")
    
    session["video_url"] = ""
    try: url = session["playlist_url"]
    except Exception: url = ""
    return render_template("playlist.html", user=current_user, url=url)

@views.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        if "convert" not in request.form:
            try:
                db.session.query(Video).delete()
                db.session.commit()
                flash("Cleared History", category="success")
                return render_template("history.html", user=current_user)
            except Exception:
                db.session.rollback()
                flash("Could not clear history.", category="error")
        else:
            redirect_page = convert_video_redirect("convert")
            return redirect(url_for(redirect_page))
    
    session.clear()
    return render_template("history.html", user=current_user)

@views.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        if request.form["search"] == "video" or request.form["search"] == "playlist":
            title = request.form.get("title")

            if request.form["search"] == "video":
                results = VideosSearch(title, limit=10).result()["result"]
            elif request.form["search"] == "playlist":
                results = PlaylistsSearch(title, limit=10).result()["result"]
            
            return render_template("search.html", user=current_user, results=results)
        else:
            redirect_page = convert_video_redirect("search")
            return redirect(url_for(redirect_page))

    session.clear()
    return render_template("search.html", user=current_user)

#Functions

def convert_video_redirect(form_name):
    conversion_info = request.form.get(form_name)
    url, r_type = conversion_info.split()[0], conversion_info.split()[1]
    if r_type == "video":
        session["video_url"] = url
        redirect_page = "views.video"
    else:
        session["playlist_url"] = url
        redirect_page = "views.playlist"
    return redirect_page

def zip_folder(name, path):
    zip_file_name = f"{name}.zip"
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(path):
            for file in files:
                zipf.write(os.path.join(root, file))
            
    memory_file.seek(0)
    return zip_file_name, memory_file

def download_video(yt):
    if request.form["convert"] == "mp4":
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        file_type = "mp4"
    elif request.form["convert"] == "mp3":
        video = yt.streams.filter(only_audio=True).get_audio_only()
        file_type = "mp3"

    debug_video_progress(yt, video, file_type)

    downloads_path = os.path.join(os.getcwd(), "temp")
    video.download(downloads_path)

    return video, file_type, downloads_path

def save_history(url, date, title, link_type, file_type):
    if current_user.is_authenticated:
        new_video = Video(title=title, url=url, date=date, link_type=link_type, file_type=file_type, user_id=current_user.id)
        db.session.add(new_video)
        db.session.commit()

#Debug functions

def debug_video_progress(yt, video, file_type, extra_info=""):
    highest_res = f", Highest Resolution: {video.resolution}" if file_type == "mp4" else ""
    print(f"Fetching {extra_info}\"{video.title}\"")
    print(f"[File size: {round(video.filesize * 0.000001, 2)} MB{highest_res}, Author: {yt.author}]\n")