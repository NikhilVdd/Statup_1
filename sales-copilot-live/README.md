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
- Client workspace: dashboard, companies, meetings, saved AI notes, and client timelines
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
3. After signup, the session redirects into `/dashboard`.
4. Add a client at `/companies/new`.
5. Open the client detail page and click `Start Live Call`.
6. The live assistant opens at `/app/live-call/<company_id>` with the selected company context.
7. Click `Start Call`.
8. The mock transcript streams into Flask-SocketIO.
9. The backend updates call state and returns live suggestions, call health, sentiment, close probability, objections, intent, urgency, and scheduling signals.
10. Click `Stop Call` to generate and save the post-call notes to that client.

## Dashboard And CRM

The dashboard is the main logged-in workspace:

- `/dashboard` shows company stats, upcoming meetings, recent AI notes, and a client pipeline preview.
- `/companies` shows a searchable, filterable client database.
- `/companies/new` creates a company/client with deal stage, priority, pain points, and product context.
- `/companies/<company_id>` shows the client overview, meetings, AI notes, and activity timeline.
- `/meetings` shows all scheduled meetings.
- `/meetings/new/<company_id>` schedules a meeting for a specific client.
- `/notes` lists saved AI call notes.

## Live Call Notes

Starting a call from a client page sends that company's context into the live assistant:

- Company name
- Project name
- Contact name
- Deal stage
- Known pain points
- Product or service being sold

The mock AI suggestions use that context when generating teleprompter responses. When the rep stops the call, Loading... saves the generated summary, transcript, objections, buying signals, action items, follow-up tasks, call score, close probability, and sentiment to SQLite.

If the call was launched from a meeting, the saved note is linked to that meeting. If no meeting is selected, the note is saved as a general call note for the company.

## Database

SQLite is initialized automatically on app startup through `backend/database.py`.

Current MVP tables:

- `users`
- `companies`
- `meetings`
- `call_notes`
- `activity_timeline`

The schema keeps database access isolated behind helper functions so PostgreSQL can replace SQLite later without rewriting the templates.

## What Is Mocked Right Now

- Speech-to-text is mocked in `backend/transcription_engine.py`.
- AI sales coaching is keyword-based in `backend/ai_engine.py`.
- The live call transcript is generated in `static/js/live_call.js`.
- Call state is in memory per Socket.IO session.
- Users are persisted in local SQLite through `backend/database.py`.
- CRM companies, meetings, notes, and timeline records are real SQLite records.
- Calendar booking and CRM integrations are still mocked/manual.

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
- Manual note creation and richer task management
