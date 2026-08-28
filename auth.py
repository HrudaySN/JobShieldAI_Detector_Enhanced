from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from extensions import db, mail
from models import User
from forms import (
    SignupForm,
    LoginForm,
    UsernameForm,
    PasswordResetRequestForm,
    PasswordResetForm,
)
from google_auth import oauth
from flask_mail import Message

auth_bp = Blueprint("auth", __name__)


# ---------- helpers ----------

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _send_reset_email(user):
    token = _serializer().dumps(user.email, salt="password-reset")
    reset_url = url_for("auth.reset_password_token", token=token, _external=True)

    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        # No mail server configured yet — print the link so it's usable in dev.
        current_app.logger.info("Password reset link for %s: %s", user.email, reset_url)
        print(f"[DEV] Password reset link for {user.email}: {reset_url}")
        return

    msg = Message(
        subject="Reset your password",
        recipients=[user.email],
        body=f"Click the link below to reset your password:\n\n{reset_url}\n\n"
        f"This link expires in {current_app.config['RESET_TOKEN_MAX_AGE'] // 60} minutes.",
    )
    mail.send(msg)


# ---------- signup / login / logout ----------

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower(), needs_username=True)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created. Just one more step.", "success")
        return redirect(url_for("auth.choose_username"))

    return render_template("signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back.", "success")
            if user.needs_username:
                return redirect(url_for("auth.choose_username"))
            return redirect(url_for("main.home"))
        flash("Invalid email or password.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/username", methods=["GET", "POST"])
@login_required
def choose_username():
    if not current_user.needs_username:
        return redirect(url_for("main.home"))

    form = UsernameForm(current_user_id=current_user.id)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.needs_username = False
        db.session.commit()
        flash("You're all set.", "success")
        return redirect(url_for("main.home"))

    return render_template("signup_username.html", form=form)


# ---------- Google OAuth ----------

@auth_bp.route("/google/login")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    print("Redirect URI:", redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo") or oauth.google.parse_id_token(token)

    google_id = user_info["sub"]
    email = user_info["email"].lower()

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        # Link to an existing email/password account, or create a new one.
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
        else:
            user = User(email=email, google_id=google_id, needs_username=True)
            db.session.add(user)
        db.session.commit()

    login_user(user)
    if user.needs_username:
        return redirect(url_for("auth.choose_username"))
    return redirect(url_for("main.home"))


# ---------- password reset ----------

@auth_bp.route("/password-reset", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        # Always show the same message, whether or not the account exists,
        # so we don't leak which emails are registered.
        if user and user.password_hash:
            _send_reset_email(user)
        return redirect(url_for("auth.reset_password_done"))

    return render_template("password_reset.html", form=form)


@auth_bp.route("/password-reset/done")
def reset_password_done():
    return render_template("password_reset_done.html")


@auth_bp.route("/password-reset/<token>", methods=["GET", "POST"])
def reset_password_token(token):
    try:
        email = _serializer().loads(
            token, salt="password-reset", max_age=current_app.config["RESET_TOKEN_MAX_AGE"]
        )
    except (BadSignature, SignatureExpired):
        return render_template("password_reset_from_key.html", token_fail=True, form=None)

    user = User.query.filter_by(email=email).first()
    if not user:
        return render_template("password_reset_from_key.html", token_fail=True, form=None)

    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password1.data)
        db.session.commit()
        return redirect(url_for("auth.reset_password_complete"))

    return render_template("password_reset_from_key.html", token_fail=False, form=form)


@auth_bp.route("/password-reset/complete")
def reset_password_complete():
    return render_template("password_reset_from_key_done.html")
