from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import User

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def view_profile():
    return render_template("profile.html", active_page="profile")


@profile_bp.route("/edit", methods=["POST"])
@login_required
def edit_profile():
    new_username = (request.form.get("username") or "").strip()

    if new_username and new_username != current_user.username:
        if User.query.filter(User.username == new_username, User.id != current_user.id).first():
            flash("That username is taken.", "error")
            return redirect(url_for("profile.view_profile"))
        current_user.username = new_username
        db.session.commit()
        flash("Profile updated.", "success")

    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    if not current_user.password_hash:
        flash("Your account signs in with Google — there's no password to change here.", "error")
        return redirect(url_for("profile.view_profile"))

    current_pw = request.form.get("current_password") or ""
    new_pw = request.form.get("new_password") or ""
    confirm_pw = request.form.get("confirm_password") or ""

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "error")
    elif len(new_pw) < 8:
        flash("New password must be at least 8 characters.", "error")
    elif new_pw != confirm_pw:
        flash("New password and confirmation don't match.", "error")
    else:
        current_user.set_password(new_pw)
        db.session.commit()
        flash("Password changed.", "success")

    return redirect(url_for("profile.view_profile"))