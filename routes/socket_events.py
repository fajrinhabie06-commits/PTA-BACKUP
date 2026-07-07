"""Socket.IO event handlers."""

from flask_socketio import emit, join_room
from flask_login import current_user
from models import Sangga


def register_socket_events(socketio):

    @socketio.on("connect")
    def on_connect():
        """Client connected."""
        sanggas = Sangga.query.all()
        leaderboard = sorted(
            [s.to_dict() for s in sanggas],
            key=lambda x: x["total_xp"],
            reverse=True,
        )
        emit("leaderboard_update", {"leaderboard": leaderboard})

    @socketio.on("join_quiz")
    def on_join_quiz(data):
        quiz_id = data.get("quiz_id")
        join_room(f"quiz_{quiz_id}")

    @socketio.on("disconnect")
    def on_disconnect():
        pass
