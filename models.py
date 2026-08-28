from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)

    # Null for accounts created via Google (they never set a local password)
    password_hash = db.Column(db.String(255), nullable=True)

    # Set when the account was created/linked through Google Sign-In
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # True until the user finishes the "choose a username" step after signup
    needs_username = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class JobAnalysis(db.Model):
    __tablename__ = "job_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    job_text = db.Column(db.Text, nullable=False)
    job_url = db.Column(db.String(1000), nullable=True)
    recruiter_email = db.Column(db.String(255), nullable=True)
    company_website = db.Column(db.String(1000), nullable=True)
    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    verdict = db.Column(db.String(100), nullable=False)
    result_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("job_analyses", lazy="dynamic"))
