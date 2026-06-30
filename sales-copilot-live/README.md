# Loading...

Loading... is an MVP skeleton for a real-time AI sales teleprompter. The product is designed for consent-based phone and video sales calls: it listens live, streams transcript updates, detects objections and buying signals, scores the call, and prompts the salesperson with what to say next.

This version uses mock transcription and keyword-based AI logic, but the structure is ready for browser microphone streaming, phone-call audio, speech-to-text services, OpenAI-powered suggestions, and a future Mac desktop wrapper.

## Tech Stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python Flask
- Real-time communication: Flask-SocketIO
- Auth: simple Flask session auth
- Database: SQLite locally, optional Firebase Firestore for production, isolated behind `backend/database.py`
- Demo audio/transcription: mocked
- AI suggestions: OpenAI-compatible provider when configured, keyword mock fallback otherwise

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
9. Optionally type a buyer sentence into the manual transcript box to test the teleprompter against your own sales scenario.
10. The backend updates call state and returns live suggestions, call health, sentiment, close probability, objections, intent, urgency, and scheduling signals.
11. Click `Stop Call` to generate and save the post-call notes to that client.

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

AI suggestions use that context when generating teleprompter responses. When the rep stops the call, Loading... saves the generated summary, transcript, objections, buying signals, action items, follow-up tasks, call score, close probability, and sentiment to the configured database.

If the call was launched from a meeting, the saved note is linked to that meeting. If no meeting is selected, the note is saved as a general call note for the company.

## Real AI Teleprompter

The teleprompter has a provider layer in `backend/ai_provider.py`.

By default, Loading... runs in `auto` mode:

- If `OPENAI_API_KEY` is set, live suggestions come from the configured AI model.
- If no key is set, the app falls back to the local keyword mock engine.
- If the provider has an error during a call, the app keeps running and shows a mock fallback suggestion.

To enable real AI suggestions:

```bash
cp .env.example .env
```

Then set:

```text
AI_PROVIDER=auto
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-api-key-here
```

Restart the Flask app after changing `.env`.

On the live-call page, the pill in the top bar shows whether the current call is using `Real AI`, `Mock AI`, or `Mock fallback`.

## Database

SQLite is the default local database and is initialized automatically on app startup through `backend/database.py`.

Current MVP data models:

- `users`
- `companies`
- `meetings`
- `call_notes`
- `activity_timeline`

The database access is isolated behind helper functions, so the same Flask routes can use SQLite locally or Firebase Firestore in production.

### Firebase Firestore

To use Firebase Firestore instead of SQLite:

1. Create a Firebase project.
2. Enable Firestore Database.
3. Create a Firebase Admin service account key.
4. Save the key locally outside git, for example:

```text
firebase-service-account.json
```

5. Update `.env`:

```text
DATABASE_PROVIDER=firebase
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=/absolute/path/to/firebase-service-account.json
```

You can also provide the service account as JSON in `FIREBASE_CREDENTIALS_JSON` for hosts that store secrets as environment variables.

Never commit Firebase service account JSON files. `.gitignore` already ignores common service account filenames.

Firestore collections used by the app:

- `users`
- `companies`
- `meetings`
- `call_notes`
- `activity_timeline`
- `_metadata` for numeric ID counters

## What Is Mocked Right Now

- Speech-to-text is mocked in `backend/transcription_engine.py`.
- AI sales coaching uses the real AI provider when `OPENAI_API_KEY` is configured; otherwise it falls back to keyword-based logic in `backend/ai_engine.py`.
- The live call transcript is generated in `static/js/live_call.js`.
- Call state is in memory per Socket.IO session.
- Users are persisted through `backend/database.py`.
- CRM companies, meetings, notes, and timeline records are real database records.
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

Real AI suggestions are routed through `backend/ai_provider.py`. Keep the same response shape so the frontend remains stable while the intelligence improves.

## Future Integrations

- Twilio Voice
- Browser microphone streaming
- Deepgram, AssemblyAI, OpenAI speech-to-text, or Whisper
- OpenAI API for real-time suggestions
- CRM integrations
- Calendar integrations
- Firebase security rules and production auth hardening
- PostgreSQL replacement for SQLite if needed later
- Electron or Tauri wrapper for Mac
- Manual note creation and richer task management
