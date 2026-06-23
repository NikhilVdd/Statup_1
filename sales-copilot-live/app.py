from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

from backend.ai_engine import generate_live_sales_suggestion
from backend.call_state import CallState
from backend.transcription_engine import process_audio_chunk
from backend.utils import build_call_summary

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "closecue-demo-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

call_sessions = {}


def get_call_state():
    sid = request.sid
    if sid not in call_sessions:
        call_sessions[sid] = CallState()
    return call_sessions[sid]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/live-call")
def live_call():
    return render_template("live_call.html")


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
