"""Participant Blueprint."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Sangga, Day, Mission, MissionSubmission, Quiz

participant_bp = Blueprint("participant", __name__)


@participant_bp.route("/")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    sanggas = Sangga.query.order_by(Sangga.xp.desc()).all()
    days = Day.query.order_by(Day.day_number).all()
    active_quiz = Quiz.query.filter_by(is_active=True).first()
    my_sangga = current_user.sangga
    my_submissions = []
    if my_sangga:
        my_submissions = MissionSubmission.query.filter_by(
            sangga_id=my_sangga.id
        ).order_by(MissionSubmission.submitted_at.desc()).all()

    # Rank of my sangga
    my_rank = None
    if my_sangga:
        sorted_s = sorted(sanggas, key=lambda s: s.total_xp, reverse=True)
        my_rank = next((i + 1 for i, s in enumerate(sorted_s) if s.id == my_sangga.id), None)

    return render_template(
        "dashboard.html",
        sanggas=sanggas,
        days=days,
        active_quiz=active_quiz,
        my_sangga=my_sangga,
        my_submissions=my_submissions,
        my_rank=my_rank,
    )


@participant_bp.route("/submit-mission", methods=["POST"])
@login_required
def submit_mission():
    if current_user.is_admin:
        flash("Admin tidak bisa submit misi.", "warning")
        return redirect(url_for("admin.dashboard"))

    mission_id = int(request.form.get("mission_id", 0))
    link = request.form.get("link", "").strip()

    if not link:
        flash("Link bukti tidak boleh kosong.", "danger")
        return redirect(url_for("participant.dashboard"))

    mission = Mission.query.get_or_404(mission_id)
    if mission.day.is_locked:
        flash("Hari ini masih terkunci. Tunggu Admin membuka akses. 🔒", "warning")
        return redirect(url_for("participant.dashboard"))

    if not current_user.sangga_id:
        flash("Kamu belum terdaftar di Sangga manapun.", "danger")
        return redirect(url_for("participant.dashboard"))

    # Check duplicate
    existing = MissionSubmission.query.filter_by(
        mission_id=mission_id, sangga_id=current_user.sangga_id
    ).first()
    if existing:
        flash("Sangga kamu sudah pernah submit misi ini.", "warning")
        return redirect(url_for("participant.dashboard"))

    sub = MissionSubmission(
        mission_id=mission_id,
        sangga_id=current_user.sangga_id,
        submitted_by_id=current_user.id,
        link=link,
    )
    db.session.add(sub)
    db.session.commit()
    flash("✅ Submission berhasil dikirim! Tunggu review dari Admin.", "success")
    return redirect(url_for("participant.dashboard"))
