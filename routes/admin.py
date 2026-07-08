"""Admin Blueprint – full control panel."""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Sangga, Day, Mission, MissionSubmission, Quiz, QuizQuestion, XPLog, QuizAnswer

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Akses ditolak. Area khusus Admin.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────────
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    sanggas = Sangga.query.order_by(Sangga.xp.desc()).all()
    users = User.query.filter_by(role="participant").order_by(User.full_name).all()
    days = Day.query.order_by(Day.day_number).all()
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    missions = Mission.query.order_by(Mission.day_id, Mission.id).all()
    pending_subs = MissionSubmission.query.filter_by(status="pending").count()
    submissions = MissionSubmission.query.order_by(MissionSubmission.submitted_at.desc()).limit(20).all()
    xp_logs = XPLog.query.order_by(XPLog.created_at.desc()).limit(20).all()

    return render_template(
        "admin.html",
        sanggas=sanggas,
        users=users,
        days=days,
        quizzes=quizzes,
        missions=missions,
        pending_subs=pending_subs,
        submissions=submissions,
        xp_logs=xp_logs,
    )


# ── Sangga Management ──────────────────────────────────────────────────────────
@admin_bp.route("/sangga/add", methods=["POST"])
@login_required
@admin_required
def add_sangga():
    name = request.form.get("name", "").strip()
    emoji = request.form.get("emoji", "⚜️").strip()
    if not name:
        flash("Nama Sangga tidak boleh kosong.", "danger")
        return redirect(url_for("admin.dashboard"))
    if Sangga.query.filter_by(name=name).first():
        flash("Nama Sangga sudah ada.", "warning")
        return redirect(url_for("admin.dashboard"))
    s = Sangga(name=name, emoji=emoji)
    db.session.add(s)
    db.session.commit()
    flash(f"Sangga '{name}' berhasil ditambahkan! ✅", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/sangga/<int:sid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_sangga(sid):
    s = Sangga.query.get_or_404(sid)
    # Unlink users first
    for u in s.members:
        u.sangga_id = None
    db.session.delete(s)
    db.session.commit()
    flash(f"Sangga '{s.name}' dihapus.", "info")
    return redirect(url_for("admin.dashboard"))


# ── XP Control ─────────────────────────────────────────────────────────────────
@admin_bp.route("/sangga/<int:sid>/xp", methods=["POST"])
@login_required
@admin_required
def adjust_xp(sid):
    s = Sangga.query.get_or_404(sid)
    amount = int(request.form.get("amount", 0))
    reason = request.form.get("reason", "Manual adjustment").strip()
    s.xp = max(0, s.xp + amount)
    log = XPLog(sangga_id=sid, admin_id=current_user.id, amount=amount, reason=reason)
    db.session.add(log)
    db.session.commit()
    action = f"+{amount}" if amount >= 0 else str(amount)
    flash(f"XP Sangga '{s.name}' diubah {action}. Alasan: {reason}", "success")
    return redirect(url_for("admin.dashboard"))


# ── User Management ────────────────────────────────────────────────────────────
@admin_bp.route("/user/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    username = request.form.get("username", "").strip()
    full_name = request.form.get("full_name", "").strip()
    password = request.form.get("password", "").strip()
    sangga_id = request.form.get("sangga_id")

    if not all([username, full_name, password]):
        flash("Semua field wajib diisi.", "danger")
        return redirect(url_for("admin.dashboard"))

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' sudah digunakan.", "warning")
        return redirect(url_for("admin.dashboard"))

    u = User(
        username=username,
        full_name=full_name,
        role="participant",
        sangga_id=int(sangga_id) if sangga_id else None,
    )
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    flash(f"Peserta '{full_name}' berhasil ditambahkan! ✅", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/user/<int:uid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(uid):
    u = User.query.get_or_404(uid)
    if u.is_admin:
        flash("Tidak bisa menghapus akun Admin.", "danger")
        return redirect(url_for("admin.dashboard"))

    full_name = u.full_name

    # Bersihkan dulu data-data yang masih terhubung ke user ini,
    # supaya tidak kena foreign key constraint error (500) saat dihapus
    QuizAnswer.query.filter_by(user_id=u.id).delete()
    MissionSubmission.query.filter_by(submitted_by_id=u.id).delete()

    db.session.delete(u)
    db.session.commit()
    flash(f"Peserta '{full_name}' dihapus.", "info")
    return redirect(url_for("admin.dashboard"))


# ── Day / Gatekeeper ───────────────────────────────────────────────────────────
@admin_bp.route("/day/<int:did>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_day(did):
    d = Day.query.get_or_404(did)
    d.is_locked = not d.is_locked
    db.session.commit()
    status = "🔒 dikunci" if d.is_locked else "🔓 dibuka"
    flash(f"Hari {d.day_number} sekarang {status}.", "success")
    return redirect(url_for("admin.dashboard"))


# ── Mission Management ─────────────────────────────────────────────────────────
@admin_bp.route("/mission/add", methods=["POST"])
@login_required
@admin_required
def add_mission():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    link = request.form.get("link", "").strip()
    day_id = request.form.get("day_id")
    xp_reward = int(request.form.get("xp_reward", 50))

    if not title or not day_id:
        flash("Judul misi dan Hari wajib diisi.", "danger")
        return redirect(url_for("admin.dashboard"))

    m = Mission(
        title=title,
        description=description,
        link=link,
        day_id=int(day_id),
        xp_reward=xp_reward,
    )
    db.session.add(m)
    db.session.commit()
    flash(f"Misi '{title}' berhasil dibuat! ✅", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/mission/<int:mid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_mission(mid):
    m = Mission.query.get_or_404(mid)
    title = m.title
    db.session.delete(m)
    db.session.commit()
    flash(f"Misi '{title}' dihapus.", "info")
    return redirect(url_for("admin.dashboard"))


# ── Submission Review ──────────────────────────────────────────────────────────
@admin_bp.route("/submission/<int:sub_id>/review", methods=["POST"])
@login_required
@admin_required
def review_submission(sub_id):
    from datetime import datetime, timezone
    sub = MissionSubmission.query.get_or_404(sub_id)
    action = request.form.get("action")  # approve | reject

    if action == "approve":
        sub.status = "approved"
        sub.xp_awarded = sub.mission.xp_reward
        sub.sangga.xp += sub.xp_awarded
        sub.reviewed_at = datetime.now(timezone.utc)
        flash(f"Submission disetujui! +{sub.xp_awarded} XP untuk {sub.sangga.name}. ✅", "success")
    elif action == "reject":
        sub.status = "rejected"
        sub.reviewed_at = datetime.now(timezone.utc)
        flash("Submission ditolak.", "warning")

    db.session.commit()
    return redirect(url_for("admin.dashboard"))


# ── Quiz Management ────────────────────────────────────────────────────────────
@admin_bp.route("/quiz/add", methods=["POST"])
@login_required
@admin_required
def add_quiz():
    title = request.form.get("title", "").strip()
    time_limit = int(request.form.get("time_limit", 30))
    if not title:
        flash("Judul kuis wajib diisi.", "danger")
        return redirect(url_for("admin.dashboard"))
    q = Quiz(title=title, time_limit_seconds=time_limit)
    db.session.add(q)
    db.session.commit()
    flash(f"Kuis '{title}' berhasil dibuat!", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/quiz/<int:qid>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_quiz(qid):
    q = Quiz.query.get_or_404(qid)
    new_status = not q.is_active  # tentukan status baru SEBELUM di-reset massal
    # Deactivate all others first
    Quiz.query.update({"is_active": False})
    q.is_active = new_status
    db.session.commit()
    status = "✅ Aktif" if q.is_active else "⏸ Nonaktif"
    flash(f"Kuis '{q.title}' sekarang {status}.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/quiz/<int:qid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_quiz(qid):
    q = Quiz.query.get_or_404(qid)
    title = q.title
    db.session.delete(q)
    db.session.commit()
    flash(f"Kuis '{title}' dihapus.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/quiz/<int:qid>/question/add", methods=["POST"])
@login_required
@admin_required
def add_question(qid):
    q = Quiz.query.get_or_404(qid)
    text = request.form.get("text", "").strip()
    option_a = request.form.get("option_a", "").strip()
    option_b = request.form.get("option_b", "").strip()
    option_c = request.form.get("option_c", "").strip()
    option_d = request.form.get("option_d", "").strip()
    correct = request.form.get("correct_option", "A").upper()
    base_xp = int(request.form.get("base_xp", 100))

    if not all([text, option_a, option_b, option_c, option_d]):
        flash("Semua field soal wajib diisi.", "danger")
        return redirect(url_for("admin.dashboard"))

    order = q.questions.count()
    qq = QuizQuestion(
        quiz_id=qid,
        text=text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct,
        base_xp=base_xp,
        order_index=order,
    )
    db.session.add(qq)
    db.session.commit()
    flash(f"Soal #{order + 1} berhasil ditambahkan ke kuis '{q.title}'! ✅", "success")
    return redirect(url_for("admin.dashboard"))