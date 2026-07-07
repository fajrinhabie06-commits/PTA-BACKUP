"""API Blueprint – JSON endpoints for dynamic data."""

from flask import Blueprint, jsonify
from flask_login import login_required
from models import db, Sangga, Quiz, QuizQuestion
import time

api_bp = Blueprint("api", __name__)

# Cache sederhana untuk leaderboard, biar server gak query ulang
# database di setiap request kalau ada banyak siswa polling bersamaan.
_leaderboard_cache = {"data": None, "timestamp": 0}
CACHE_DURATION = 3  # detik


@api_bp.route("/leaderboard")
def leaderboard():
    now = time.time()
    if _leaderboard_cache["data"] is None or (now - _leaderboard_cache["timestamp"]) > CACHE_DURATION:
        sanggas = Sangga.query.all()
        data = sorted([s.to_dict() for s in sanggas], key=lambda x: x["total_xp"], reverse=True)
        _leaderboard_cache["data"] = data
        _leaderboard_cache["timestamp"] = now
    return jsonify({"leaderboard": _leaderboard_cache["data"]})


@api_bp.route("/quiz/<int:qid>/questions")
@login_required
def quiz_questions(qid):
    q = Quiz.query.get_or_404(qid)
    if not q.is_active:
        return jsonify({"error": "Kuis tidak aktif"}), 403
    questions = [qq.to_dict_safe() for qq in q.questions.order_by(QuizQuestion.order_index)]
    return jsonify({"questions": questions, "time_limit": q.time_limit_seconds})