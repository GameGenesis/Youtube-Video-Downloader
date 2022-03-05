from flask import Blueprint, render_template, request, flash, redirect, session, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("views.video"))
            else:
                flash("Incorrect password.", category="error")
        else:
            flash("User email does not exist.", category="error")

    return render_template("login.html", user=current_user)

@auth.route("/logout")
@login_required
def logout():
    session.clear()
    logout_user()
    flash("Logged out successfuly!", category="success")
    return redirect(url_for("views.video"))

@auth.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        user = User.query.filter_by(email=email).first()
        if user:
            flash("User already exists.", category="error")
        elif len(email) < 4:
            flash("Email is invalid.", category="error")
        elif len(name) < 2:
            flash("Name is invalid. Must contin at least 2 characters.", category="error")
        elif password1 != password2:
            flash("Passwords do not match.", category="error")
        elif len(password1) < 6:
            flash("Password is invalid. Must contin at least 6 characters.", category="error")
        else:
            new_user = User(email=email, name=name, password=generate_password_hash(password1, method="sha256"))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created successfully!", category="success")
            return redirect(url_for("views.video"))

    return render_template("sign_up.html", user=current_user)

@auth.route("/delete-account", methods=["GET", "POST"])
@login_required
def delete_account():
    if request.method == "POST":
        confirm_message = request.form.get("confirm-message")
        if confirm_message != "delete-account":
            flash("Confirmation message is incorrect.", category="error")
            return render_template("delete_account.html", user=current_user) 

        try:
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash("Deleted account!", category="success")
            return redirect(url_for("views.video"))
        except Exception:
            flash("Could not delete account.", category="error")
    return render_template("delete_account.html", user=current_user)