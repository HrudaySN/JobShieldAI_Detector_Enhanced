import json
from datetime import datetime
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from extensions import db
from job_analyzer import model
from models import JobAnalysis

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html", active_page="home")


@main_bp.route("/detector")
@login_required
def detector():
    return render_template("detector.html", active_page="detector", training_examples=model.examples)


@main_bp.route("/api/analyze-job", methods=["POST"])
@login_required
def analyze_job():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(model.analyze(payload.get("text", ""), payload))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@main_bp.route("/api/save-analysis", methods=["POST"])
@login_required
def save_analysis():
    payload = request.get_json(silent=True) or {}
    result = payload.get("result") or {}
    text = (payload.get("text") or "").strip()
    if not text or not result:
        return jsonify({"error": "Nothing to save yet."}), 400
    record = JobAnalysis(
        user_id=current_user.id,
        job_text=text[:10000],
        job_url=(payload.get("job_url") or "")[:1000] or None,
        recruiter_email=(payload.get("recruiter_email") or "")[:255] or None,
        company_website=(payload.get("company_website") or "")[:1000] or None,
        risk_score=int(result.get("risk_score", 0)),
        risk_level=result.get("risk_level", "Medium"),
        verdict=result.get("verdict", "Needs review"),
        result_json=json.dumps(result),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"ok": True, "id": record.id})


@main_bp.route("/api/analysis/<int:analysis_id>")
@login_required
def get_analysis(analysis_id):
    record = JobAnalysis.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    return jsonify({
        "id": record.id,
        "text": record.job_text,
        "job_url": record.job_url,
        "recruiter_email": record.recruiter_email,
        "company_website": record.company_website,
        "created_at": record.created_at.isoformat(),
        "result": json.loads(record.result_json),
    })


@main_bp.route("/resume-screening")
@login_required
def resume_screen():
    return render_template("resume.html", active_page="resume")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    analyses = JobAnalysis.query.filter_by(user_id=current_user.id)
    total = analyses.count()
    high = analyses.filter(JobAnalysis.risk_level == "High").count()
    medium = analyses.filter(JobAnalysis.risk_level == "Medium").count()
    low = analyses.filter(JobAnalysis.risk_level == "Low").count()
    recent = analyses.order_by(JobAnalysis.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", active_page="dashboard", stats={"total": total, "high": high, "medium": medium, "low": low}, recent=recent)


@main_bp.route("/history")
@login_required
def history():
    analyses = JobAnalysis.query.filter_by(user_id=current_user.id).order_by(JobAnalysis.created_at.desc()).all()
    return render_template("history.html", active_page="history", analyses=analyses)


@main_bp.route("/support")
def support():
    return render_template("support.html", active_page="support")
