from flask import Blueprint, render_template
from flask_login import login_required, current_user

views = Blueprint("views", __name__)

@views.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html", user=current_user)

@views.route("/history", methods=["GET", "POST"])
@login_required
def history():
    return render_template("history.html", user=current_user)