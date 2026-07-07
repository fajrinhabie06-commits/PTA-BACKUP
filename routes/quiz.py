"""Quiz Blueprint – real-time quiz with speed-based scoring."""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Quiz, QuizQuestion, QuizAnswer, Sangga
from flask_socketio import emit
import time

quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.route("/")
@login_required
def index():
    active_quiz = Quiz.query.filter_by(is_active=True).first()
    if not active_quiz:
        flash("Belum ada kuis aktif saat ini. 📋", "info")
        return redirect(url_for("participant.dashboard"))
    return render_template("quiz.html", quiz=active_quiz)


@quiz_bp.route("/submit-answer", methods=["POST"])
@login_required
def submit_answer():
    """Process a single quiz answer with speed-based XP calculation."""
    data = request.get_json()
    question_id = data.get("question_id")
    selected = data.get("selected_option", "").upper()
    response_time_ms = int(data.get("response_time_ms", 30000))

    if not question_id or selected not in ("A", "B", "C", "D"):
        return jsonify({"error": "Data tidak valid"}), 400

    qq = QuizQuestion.query.get_or_404(question_id)

    # Prevent duplicate answers
    existing = QuizAnswer.query.filter_by(
        user_id=current_user.id, question_id=question_id
    ).first()
    if existing:
        return jsonify({"error": "Sudah dijawab", "already_answered": True}), 400

    is_correct = (selected == qq.correct_option)
    xp_earned = 0

    if is_correct:
        time_limit_ms = qq.quiz.time_limit_seconds * 1000
        # Speed bonus: faster = more XP (min 20% if correct but slow)
        speed_ratio = max(0, 1 - (response_time_ms / time_limit_ms))
        xp_earned = int(qq.base_xp * (0.2 + 0.8 * speed_ratio))
        xp_earned = max(20, min(xp_earned, qq.base_xp))  # clamp 20–100

    answer = QuizAnswer(
        user_id=current_user.id,
        question_id=question_id,
        selected_option=selected,
        is_correct=is_correct,
        xp_earned=xp_earned,
        response_time_ms=response_time_ms,
    )
    db.session.add(answer)

    # Add XP to user
    current_user.quiz_xp += xp_earned
    db.session.commit()

    # Broadcast leaderboard update via Socket.IO
    sanggas = Sangga.query.all()
    leaderboard = sorted([s.to_dict() for s in sanggas], key=lambda x: x["total_xp"], reverse=True)
    socketio.emit("leaderboard_update", {"leaderboard": leaderboard})

    return jsonify({
        "correct": is_correct,
        "correct_option": qq.correct_option,
        "xp_earned": xp_earned,
        "response_time_ms": response_time_ms,
        "user_total_xp": current_user.quiz_xp,
    })


@quiz_bp.route("/leaderboard")
def leaderboard():
    sanggas = Sangga.query.all()
    sorted_sanggas = sorted(sanggas, key=lambda s: s.total_xp, reverse=True)
    return render_template("leaderboard.html", sanggas=sorted_sanggas)
