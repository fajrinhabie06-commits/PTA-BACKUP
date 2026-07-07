"""
Database Models – PTA Scout Adventure 2026
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
class Sangga(db.Model):
    """A team (sangga) of scouts."""
    __tablename__ = "sangga"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    emoji = db.Column(db.String(10), default="⚜️")
    xp = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    members = db.relationship("User", back_populates="sangga", lazy="dynamic")
    submissions = db.relationship("MissionSubmission", back_populates="sangga", lazy="dynamic")

    @property
    def member_count(self):
        return self.members.count()

    @property
    def total_quiz_xp(self):
        return sum(u.quiz_xp for u in self.members)

    @property
    def total_xp(self):
        return self.xp + self.total_quiz_xp

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "emoji": self.emoji,
            "xp": self.xp,
            "quiz_xp": self.total_quiz_xp,
            "total_xp": self.total_xp,
            "member_count": self.member_count,
        }

    def __repr__(self):
        return f"<Sangga {self.name}>"


# ─────────────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    """Individual scout participant or admin."""
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default="participant")  # admin | participant
    quiz_xp = db.Column(db.Integer, default=0)
    sangga_id = db.Column(db.Integer, db.ForeignKey("sangga.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sangga = db.relationship("Sangga", back_populates="members")
    quiz_answers = db.relationship("QuizAnswer", back_populates="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "quiz_xp": self.quiz_xp,
            "sangga_id": self.sangga_id,
            "sangga_name": self.sangga.name if self.sangga else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


# ─────────────────────────────────────────────────────────────────────────────
class Day(db.Model):
    """Competition day – controls mission access."""
    __tablename__ = "day"

    id = db.Column(db.Integer, primary_key=True)
    day_number = db.Column(db.Integer, nullable=False, unique=True)
    is_locked = db.Column(db.Boolean, default=True)
    label = db.Column(db.String(80), default="")

    missions = db.relationship("Mission", back_populates="day", lazy="dynamic")


# ─────────────────────────────────────────────────────────────────────────────
class Mission(db.Model):
    """A task/challenge assigned to a day."""
    __tablename__ = "mission"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    link = db.Column(db.String(500), default="")  # Resource link
    xp_reward = db.Column(db.Integer, default=50)
    day_id = db.Column(db.Integer, db.ForeignKey("day.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    day = db.relationship("Day", back_populates="missions")
    submissions = db.relationship("MissionSubmission", back_populates="mission", lazy="dynamic")

    def __repr__(self):
        return f"<Mission {self.title}>"


# ─────────────────────────────────────────────────────────────────────────────
class MissionSubmission(db.Model):
    """Submission evidence for a mission by a sangga."""
    __tablename__ = "mission_submission"

    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(db.Integer, db.ForeignKey("mission.id"), nullable=False)
    sangga_id = db.Column(db.Integer, db.ForeignKey("sangga.id"), nullable=False)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    xp_awarded = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime, nullable=True)

    mission = db.relationship("Mission", back_populates="submissions")
    sangga = db.relationship("Sangga", back_populates="submissions")
    submitted_by = db.relationship("User")

    def __repr__(self):
        return f"<Submission {self.id} – {self.status}>"


# ─────────────────────────────────────────────────────────────────────────────
class Quiz(db.Model):
    """A quiz session."""
    __tablename__ = "quiz"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    day_id = db.Column(db.Integer, db.ForeignKey("day.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    time_limit_seconds = db.Column(db.Integer, default=30)  # per question
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    questions = db.relationship("QuizQuestion", back_populates="quiz",
                                 cascade="all, delete-orphan", lazy="dynamic",
                                 order_by="QuizQuestion.order_index")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "is_active": self.is_active,
            "time_limit_seconds": self.time_limit_seconds,
            "question_count": self.questions.count(),
        }


# ─────────────────────────────────────────────────────────────────────────────
class QuizQuestion(db.Model):
    """A single multiple-choice question."""
    __tablename__ = "quiz_question"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A/B/C/D
    base_xp = db.Column(db.Integer, default=100)
    order_index = db.Column(db.Integer, default=0)

    quiz = db.relationship("Quiz", back_populates="questions")
    answers = db.relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict_safe(self):
        """Returns question without correct answer (for participants)."""
        return {
            "id": self.id,
            "text": self.text,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "option_c": self.option_c,
            "option_d": self.option_d,
            "base_xp": self.base_xp,
            "time_limit": self.quiz.time_limit_seconds,
        }

    def to_dict_admin(self):
        d = self.to_dict_safe()
        d["correct_option"] = self.correct_option
        return d


# ─────────────────────────────────────────────────────────────────────────────
class QuizAnswer(db.Model):
    """An individual's answer to a quiz question."""
    __tablename__ = "quiz_answer"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_question.id"), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    xp_earned = db.Column(db.Integer, default=0)
    response_time_ms = db.Column(db.Integer, default=0)  # milliseconds
    answered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="quiz_answers")
    question = db.relationship("QuizQuestion", back_populates="answers")

    __table_args__ = (
        db.UniqueConstraint("user_id", "question_id", name="uq_user_question"),
    )


# ─────────────────────────────────────────────────────────────────────────────
class XPLog(db.Model):
    """Audit log for manual XP changes."""
    __tablename__ = "xp_log"

    id = db.Column(db.Integer, primary_key=True)
    sangga_id = db.Column(db.Integer, db.ForeignKey("sangga.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # positive = bonus, negative = penalty
    reason = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sangga = db.relationship("Sangga")
    admin = db.relationship("User")
