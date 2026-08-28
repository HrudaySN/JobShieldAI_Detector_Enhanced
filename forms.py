from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from models import User


class SignupForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password1 = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")]
    )
    password2 = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password1", message="Passwords must match.")],
    )
    submit = SubmitField("Sign Up")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class UsernameForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    submit = SubmitField("Continue")

    def __init__(self, current_user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user_id = current_user_id

    def validate_username(self, field):
        existing = User.query.filter_by(username=field.data).first()
        if existing and existing.id != self.current_user_id:
            raise ValidationError("That username is taken.")


class PasswordResetRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")


class PasswordResetForm(FlaskForm):
    password1 = PasswordField(
        "New password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")]
    )
    password2 = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password1", message="Passwords must match.")],
    )
    submit = SubmitField("Change password")
