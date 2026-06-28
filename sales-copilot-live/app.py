import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

from backend.ai_engine import generate_live_sales_suggestion
from backend.call_state import CallState
from backend.database import create_user, find_user_by_id, init_db, verify_user
from backend.transcription_engine import process_audio_chunk
from backend.utils import build_call_summary

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "loading-demo-secret")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
init_db()

call_sessions = {}


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return find_user_by_id(user_id)


def login_required(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Create an account or log in to open the live assistant.")
            return redirect(url_for("login"))
        return route(*args, **kwargs)

    return wrapped


def get_call_state():
    sid = request.sid
    if sid not in call_sessions:
        call_sessions[sid] = CallState()
    return call_sessions[sid]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/download")
def download():
    return render_template("download.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Add your name, email, and a password with at least 6 characters.")
            return render_template("signup.html")

        try:
            user_id = create_user(name, email, password)
        except Exception:
            flash("That email is already registered. Try logging in instead.")
            return render_template("signup.html")

        session["user_id"] = user_id
        return redirect(url_for("app_home"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = verify_user(email, password)

        if not user:
            flash("Email or password did not match.")
            return render_template("login.html")

        session["user_id"] = user["id"]
        return redirect(url_for("app_home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user())


@app.route("/app")
@login_required
def app_home():
    return redirect(url_for("live_call"))


@app.route("/live-call")
@login_required
def live_call():
    return render_template("live_call.html", user=current_user())


@socketio.on("connect")
def handle_connect():
    call_state = get_call_state()
    emit("call_state", call_state.to_dict())


@socketio.on("disconnect")
def handle_disconnect():
    call_sessions.pop(request.sid, None)


@socketio.on("start_call")
def handle_start_call():
    call_state = get_call_state()
    call_state.start()
    emit("call_started", call_state.to_dict())


@socketio.on("stop_call")
def handle_stop_call():
    call_state = get_call_state()
    call_state.stop()
    summary = build_call_summary(call_state)
    emit("call_stopped", {"status": "inactive", "summary": summary, "call_state": call_state.to_dict()})


@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    result = process_audio_chunk(data)
    emit("audio_received", result)


@socketio.on("transcript_update")
def handle_transcript_update(data):
    call_state = get_call_state()
    speaker = data.get("speaker", "Customer")
    text = data.get("text", "").strip()

    if not text:
        emit("transcript_error", {"message": "Transcript text is required."})
        return

    call_state.add_transcript_line(speaker, text)
    suggestion = generate_live_sales_suggestion(call_state)
    call_state.add_suggestion(suggestion)

    emit("ai_suggestion", suggestion)
    emit("call_state", call_state.to_dict())


@socketio.on("request_ai_suggestion")
def handle_request_ai_suggestion():
    call_state = get_call_state()
    suggestion = generate_live_sales_suggestion(call_state)
    call_state.add_suggestion(suggestion)
    emit("ai_suggestion", suggestion)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
