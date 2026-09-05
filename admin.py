from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import User, JobAnalysis
from decorators import admin_required
from auth import _send_reset_email  # reuse the existing reset-email flow

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/dashboard.html", active_page="admin", users=users)


@admin_bp.route("/users/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    analyses = JobAnalysis.query.filter_by(user_id=user.id).order_by(JobAnalysis.created_at.desc()).all()
    return render_template("admin/user_detail.html", active_page="admin", user=user, analyses=analyses)


@admin_bp.route("/users/<int:user_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    new_username = (request.form.get("username") or "").strip()
    new_email = (request.form.get("email") or "").strip().lower()
    make_admin = request.form.get("is_admin") == "on"

    if new_username and new_username != user.username:
        if User.query.filter(User.username == new_username, User.id != user.id).first():
            flash("That username is taken.", "error")
            return redirect(url_for("admin.user_detail", user_id=user.id))
        user.username = new_username

    if new_email and new_email != user.email:
        if User.query.filter(User.email == new_email, User.id != user.id).first():
            flash("That email is already in use.", "error")
            return redirect(url_for("admin.user_detail", user_id=user.id))
        user.email = new_email

    if user.id != current_user.id:
        user.is_admin = make_admin

    db.session.commit()
    flash("User updated.", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account from here.", "error")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    JobAnalysis.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    if not user.password_hash:
        flash("This user signs in with Google and has no password to reset.", "error")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    _send_reset_email(user)
    flash(f"Password reset link sent to {user.email} (check console if mail isn't configured).", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))