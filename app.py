"""
PTA Scout Adventure 2026
========================
Production-ready Flask application for Pramuka competition management.
"""

import os
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
from models import db, User, Sangga

load_dotenv()

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
login_manager = LoginManager()


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    # ── Security & Config ──────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'scout.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

    if config:
        app.config.update(config)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # ── Extensions ─────────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Silakan login untuk melanjutkan."
    login_manager.login_message_category = "warning"
    socketio.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.participant import participant_bp
    from routes.quiz import quiz_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(participant_bp, url_prefix="/dashboard")
    app.register_blueprint(quiz_bp, url_prefix="/quiz")
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Socket Events ──────────────────────────────────────────────────────────
    from routes.socket_events import register_socket_events
    register_socket_events(socketio)

    # ── DB Init + Seed ─────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_default_data()

    return app


def _seed_default_data():
    """Create default admin + sample Sangga if DB is empty."""
    from models import User, Sangga, Day
    from werkzeug.security import generate_password_hash

    if User.query.filter_by(role="admin").first():
        return  # Already seeded

    # Default admin
    admin = User(
        username="admin",
        password_hash=generate_password_hash("admin123"),
        full_name="Administrator",
        role="admin",
    )
    db.session.add(admin)

    # Sample Sangga
    sangga_names = [
        ("Elang Emas", "🦅"),
        ("Harimau Putih", "🐯"),
        ("Naga Biru", "🐉"),
        ("Phoenix Merah", "🔥"),
    ]
    for name, emoji in sangga_names:
        s = Sangga(name=name, emoji=emoji, xp=0)
        db.session.add(s)

    # Default days
    for i in range(1, 4):
        d = Day(day_number=i, is_locked=(i > 1))
        db.session.add(d)

    db.session.commit()
    print("✅ Default data seeded. Admin: admin / admin123")


# ── Socket Events Module ───────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
