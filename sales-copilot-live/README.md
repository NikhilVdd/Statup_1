# Loading...

Loading... is an MVP skeleton for a real-time AI sales teleprompter. The product is designed for consent-based phone and video sales calls: it listens live, streams transcript updates, detects objections and buying signals, scores the call, and prompts the salesperson with what to say next.

This version uses mock transcription and keyword-based AI logic, but the structure is ready for browser microphone streaming, phone-call audio, speech-to-text services, OpenAI-powered suggestions, and a future Mac desktop wrapper.

## Tech Stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python Flask
- Real-time communication: Flask-SocketIO
- Auth: simple Flask session auth
- Database: SQLite for MVP, isolated behind `backend/database.py`
- Demo audio/transcription: mocked
- Demo AI: keyword-based mock engine

## Product Areas

- Marketing website: home, product explanation, pricing, login, signup, and Get for Mac CTA
- Product app: live sales command center with teleprompter, call score, buyer insights, scheduling assistant, notes, action items, summary, and transcript
- Compliance posture: visible consent language before call analysis

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

## App Flow

1. Visit `/`.
2. Sign up at `/signup`.
3. After signup, the session redirects into `/app`, which opens the live assistant.
4. Click `Start Call`.
5. The mock transcript streams into Flask-SocketIO.
6. The backend updates call state and returns live suggestions, call health, sentiment, close probability, objections, intent, urgency, and scheduling signals.
7. Click `Stop Call` to generate the post-call summary.

## What Is Mocked Right Now

- Speech-to-text is mocked in `backend/transcription_engine.py`.
- AI sales coaching is keyword-based in `backend/ai_engine.py`.
- The live call transcript is generated in `static/js/live_call.js`.
- Call state is in memory per Socket.IO session.
- Users are persisted in local SQLite through `backend/database.py`.

## Where To Add Real Speech-To-Text

Use `static/js/live_call.js` to capture microphone audio with `MediaRecorder` or `AudioWorklet`, then emit chunks through:

```js
socket.emit("audio_chunk", chunk);
```

Then update `backend/transcription_engine.py` to stream chunks into:

- Deepgram
- AssemblyAI
- OpenAI speech-to-text
- Whisper streaming
- Twilio Voice or another phone-call API

## Where To Add Real AI

Replace the keyword logic in `backend/ai_engine.py` with an OpenAI API call. Keep the same response shape so the frontend remains stable while the intelligence improves.

## Future Integrations

- Twilio Voice
- Browser microphone streaming
- Deepgram, AssemblyAI, OpenAI speech-to-text, or Whisper
- OpenAI API for real-time suggestions
- CRM integrations
- Calendar integrations
- PostgreSQL replacement for SQLite
- Electron or Tauri wrapper for Mac
