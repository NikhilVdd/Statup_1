# CloseCue AI

CloseCue AI is a base skeleton for a real-time AI sales teleprompter. The app is designed for live sales calls: it listens to the conversation, tracks transcript updates, detects objections and buying signals, and updates a teleprompter panel with the best thing the salesperson should say next.

This first version uses mock transcription and mock AI logic, but the architecture is ready for real browser microphone streaming, phone-call audio, speech-to-text services, and OpenAI-powered suggestions.

## Tech Stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python Flask
- Real-time communication: Flask-SocketIO
- Demo audio/transcription: mocked
- Demo AI: keyword-based mock engine

## Project Structure

```text
sales-copilot-live/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── live_call.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── live_call.js
│   └── assets/
└── backend/
    ├── __init__.py
    ├── ai_engine.py
    ├── transcription_engine.py
    ├── call_state.py
    └── utils.py
```

## Install

```bash
cd sales-copilot-live
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
python app.py
```

Open:

```text
http://localhost:5001
```

## Live Demo Flow

1. Open `/live-call`.
2. Click `Start Call`.
3. The browser asks for microphone permission.
4. A mock transcript begins streaming into the live transcript panel.
5. Each transcript line is sent to Flask-SocketIO.
6. The backend updates call state and returns a mock AI sales suggestion.
7. The teleprompter, insights, close probability, sentiment, and key moments update in real time.
8. Click `Stop Call` to generate a post-call summary.

## What Is Mocked Right Now

- Speech-to-text is mocked in `backend/transcription_engine.py`.
- AI sales coaching is keyword-based in `backend/ai_engine.py`.
- The live call transcript is generated in `static/js/live_call.js`.
- Call analytics are stored in memory per Socket.IO session.

## Where To Add Real Speech-To-Text

Use `static/js/live_call.js` to capture microphone audio with `MediaRecorder` or `AudioWorklet`, then emit chunks through:

```js
socket.emit("audio_chunk", chunk);
```

Then update `backend/transcription_engine.py` to stream those chunks into a provider such as:

- Deepgram
- AssemblyAI
- OpenAI speech-to-text
- Whisper streaming

## Where To Add Real AI

Replace the keyword logic in `backend/ai_engine.py` with an OpenAI API call. Pass the current `CallState` transcript, latest customer message, detected objections, and sales context into the model, then return the same dictionary shape used by the frontend:

```python
{
    "suggested_response": "...",
    "objection_detected": "...",
    "sentiment": "...",
    "close_probability": 0,
    "next_action": "...",
    "customer_intent": "...",
    "urgency_level": "...",
    "key_moment": "...",
}
```

## Future Integrations

- Twilio Voice or another phone-call API
- Browser microphone streaming
- Deepgram, AssemblyAI, OpenAI speech-to-text, or Whisper
- OpenAI API for real-time sales suggestions
- CRM integrations for contacts, deals, notes, and follow-ups
- Persistent call history with a database
