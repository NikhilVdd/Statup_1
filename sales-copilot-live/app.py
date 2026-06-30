import os
import json
from functools import wraps

from datetime import datetime, timezone

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

from backend.ai_engine import generate_live_sales_suggestion
from backend.ai_provider import ai_provider_status
from backend.call_state import CallState
from backend.database import (
    create_call_note,
    create_company,
    create_meeting,
    dashboard_stats,
    find_user_by_id,
    get_call_note,
    get_company,
    get_meeting,
    init_db,
    list_activity,
    list_call_notes,
    list_companies,
    list_meetings,
    create_user,
    update_company,
    verify_user,
)
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


def current_user_id():
    user = current_user()
    return user["id"] if user else None


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
    user_id = current_user_id()
    companies = list_companies(user_id)
    upcoming_meetings = list_meetings(user_id, upcoming_only=True)[:6]
    recent_notes = list_call_notes(user_id, limit=5)
    stats = dashboard_stats(user_id)
    return render_template(
        "dashboard.html",
        user=current_user(),
        companies=companies,
        upcoming_meetings=upcoming_meetings,
        recent_notes=recent_notes,
        stats=stats,
    )


@app.route("/app")
@login_required
def app_home():
    return redirect(url_for("dashboard"))


@app.route("/live-call")
@login_required
def live_call():
    return render_template("live_call.html", user=current_user(), company=None, meeting=None, ai_status=ai_provider_status())


@app.route("/app/live-call/<int:company_id>")
@login_required
def live_call_for_company(company_id):
    company = get_company(current_user_id(), company_id)
    if not company:
        abort(404)
    meeting_id = request.args.get("meeting_id", type=int)
    meeting = get_meeting(current_user_id(), meeting_id) if meeting_id else None
    return render_template("live_call.html", user=current_user(), company=company, meeting=meeting, ai_status=ai_provider_status())


@app.route("/companies")
@login_required
def companies():
    return render_template("companies.html", user=current_user(), companies=list_companies(current_user_id()))


@app.route("/companies/new", methods=["GET", "POST"])
@login_required
def company_new():
    if request.method == "POST":
        if not request.form.get("company_name", "").strip():
            flash("Company name is required.")
            return render_template("company_new.html", company=None)
        company_id = create_company(current_user_id(), request.form)
        flash("Company created.")
        return redirect(url_for("company_detail", company_id=company_id))
    return render_template("company_new.html", company=None)


@app.route("/companies/<int:company_id>")
@login_required
def company_detail(company_id):
    company = get_company(current_user_id(), company_id)
    if not company:
        abort(404)
    return render_template(
        "company_detail.html",
        user=current_user(),
        company=company,
        meetings=list_meetings(current_user_id(), company_id=company_id),
        notes=list_call_notes(current_user_id(), company_id=company_id),
        activity=list_activity(current_user_id(), company_id),
    )


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
@login_required
def company_edit(company_id):
    company = get_company(current_user_id(), company_id)
    if not company:
        abort(404)
    if request.method == "POST":
        update_company(current_user_id(), company_id, request.form)
        flash("Company updated.")
        return redirect(url_for("company_detail", company_id=company_id))
    return render_template("company_edit.html", company=company)


@app.route("/meetings")
@login_required
def meetings():
    return render_template("meetings.html", user=current_user(), meetings=list_meetings(current_user_id()))


@app.route("/meetings/new/<int:company_id>", methods=["GET", "POST"])
@login_required
def meeting_new(company_id):
    company = get_company(current_user_id(), company_id)
    if not company:
        abort(404)
    if request.method == "POST":
        if not request.form.get("title", "").strip():
            flash("Meeting title is required.")
            return render_template("meeting_new.html", company=company)
        meeting_id = create_meeting(current_user_id(), company_id, request.form)
        flash("Meeting added.")
        return redirect(url_for("meeting_detail", meeting_id=meeting_id))
    return render_template("meeting_new.html", company=company)


@app.route("/meetings/<int:meeting_id>")
@login_required
def meeting_detail(meeting_id):
    meeting = get_meeting(current_user_id(), meeting_id)
    if not meeting:
        abort(404)
    notes = list_call_notes(current_user_id(), company_id=meeting["company_id"])
    return render_template("meeting_detail.html", meeting=meeting, notes=notes)


@app.route("/notes")
@login_required
def notes():
    return render_template("notes.html", user=current_user(), notes=list_call_notes(current_user_id()))


@app.route("/notes/<int:note_id>")
@login_required
def note_detail(note_id):
    note = get_call_note(current_user_id(), note_id)
    if not note:
        abort(404)
    return render_template("note_detail.html", note=note)


@socketio.on("connect")
def handle_connect():
    call_state = get_call_state()
    emit("call_state", call_state.to_dict())


@socketio.on("disconnect")
def handle_disconnect():
    call_sessions.pop(request.sid, None)


@socketio.on("start_call")
def handle_start_call(data=None):
    data = data or {}
    call_sessions[request.sid] = CallState()
    call_state = get_call_state()
    company_id = data.get("company_id")
    meeting_id = data.get("meeting_id")
    if company_id and session.get("user_id"):
        company = get_company(session["user_id"], int(company_id))
        call_state.set_context(company, meeting_id)
    call_state.start()
    emit("call_started", call_state.to_dict())


@socketio.on("stop_call")
def handle_stop_call():
    call_state = get_call_state()
    call_state.stop()
    summary = build_call_summary(call_state)
    note_id = None
    if call_state.company_id and session.get("user_id"):
        note_id = create_call_note(
            session["user_id"],
            call_state.company_id,
            call_state.meeting_id,
            {
                "call_date": datetime.now(timezone.utc).isoformat(),
                "transcript": json.dumps(call_state.transcript),
                "summary": summary["headline"],
                "objections": ", ".join(summary["detected_objections"]),
                "buying_signals": summary.get("buying_signal", "None"),
                "pain_points": call_state.company_context.get("pain_points", ""),
                "action_items": "; ".join(summary["key_moments"]),
                "follow_up_tasks": summary["recommended_next_action"],
                "suggested_follow_up_email": summary["suggested_follow_up_email"],
                "call_score": summary["final_close_probability"],
                "close_probability": summary["final_close_probability"],
                "sentiment": summary["final_sentiment"],
            },
        )
    emit(
        "call_stopped",
        {
            "status": "inactive",
            "summary": summary,
            "call_state": call_state.to_dict(),
            "note_id": note_id,
            "note_saved": bool(note_id),
        },
    )


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
