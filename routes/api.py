"""API Blueprint – JSON endpoints for dynamic data."""

from flask import Blueprint, jsonify
from flask_login import login_required
from models import db, Sangga, Quiz, QuizQuestion

api_bp = Blueprint("api", __name__)


@api_bp.route("/leaderboard")
def leaderboard():
    sanggas = Sangga.query.all()
    data = sorted([s.to_dict() for s in sanggas], key=lambda x: x["total_xp"], reverse=True)
    return jsonify({"leaderboard": data})


@api_bp.route("/quiz/<int:qid>/questions")
@login_required
def quiz_questions(qid):
    q = Quiz.query.get_or_404(qid)
    if not q.is_active:
        return jsonify({"error": "Kuis tidak aktif"}), 403
    questions = [qq.to_dict_safe() for qq in q.questions.order_by(QuizQuestion.order_index)]
    return jsonify({"questions": questions, "time_limit": q.time_limit_seconds})
