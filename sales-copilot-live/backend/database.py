import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_URL") or str(BASE_DIR / "loading_mvp.sqlite3")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS call_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                call_id TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT,
                close_probability INTEGER DEFAULT 35,
                sentiment TEXT DEFAULT 'Neutral',
                summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                project_name TEXT,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                website TEXT,
                deal_stage TEXT DEFAULT 'New Lead',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Active',
                product_or_service TEXT,
                pain_points TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                meeting_time TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 30,
                meeting_type TEXT DEFAULT 'Discovery',
                status TEXT DEFAULT 'Upcoming',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(company_id) REFERENCES companies(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS call_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                meeting_id INTEGER,
                call_date TEXT NOT NULL,
                transcript TEXT,
                summary TEXT,
                objections TEXT,
                buying_signals TEXT,
                pain_points TEXT,
                action_items TEXT,
                follow_up_tasks TEXT,
                suggested_follow_up_email TEXT,
                call_score INTEGER,
                close_probability INTEGER,
                sentiment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(company_id) REFERENCES companies(id),
                FOREIGN KEY(meeting_id) REFERENCES meetings(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(company_id) REFERENCES companies(id)
            )
            """
        )


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def create_user(name, email, password):
    password_hash = generate_password_hash(password)
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email.lower().strip(), password_hash, created_at),
        )
        return cursor.lastrowid


def find_user_by_email(email):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()


def find_user_by_id(user_id):
    with get_connection() as connection:
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def verify_user(email, password):
    user = find_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return None
    return user


def create_activity(user_id, company_id, activity_type, description):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO activity_timeline (user_id, company_id, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, company_id, activity_type, description, utc_now()),
        )


def create_company(user_id, data):
    now = utc_now()
    fields = (
        "company_name",
        "project_name",
        "contact_name",
        "contact_email",
        "contact_phone",
        "website",
        "deal_stage",
        "priority",
        "status",
        "product_or_service",
        "pain_points",
        "notes",
    )
    values = [data.get(field, "").strip() for field in fields]
    values[6] = values[6] or "New Lead"
    values[7] = values[7] or "Medium"
    values[8] = values[8] or "Active"

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO companies (
                user_id, company_name, project_name, contact_name, contact_email,
                contact_phone, website, deal_stage, priority, status,
                product_or_service, pain_points, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, *values, now, now),
        )
        company_id = cursor.lastrowid
    create_activity(user_id, company_id, "company_created", f"Company {values[0]} created.")
    return company_id


def update_company(user_id, company_id, data):
    fields = (
        "company_name",
        "project_name",
        "contact_name",
        "contact_email",
        "contact_phone",
        "website",
        "deal_stage",
        "priority",
        "status",
        "product_or_service",
        "pain_points",
        "notes",
    )
    values = [data.get(field, "").strip() for field in fields]
    values.append(utc_now())
    values.extend([company_id, user_id])
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE companies
            SET company_name = ?, project_name = ?, contact_name = ?, contact_email = ?,
                contact_phone = ?, website = ?, deal_stage = ?, priority = ?, status = ?,
                product_or_service = ?, pain_points = ?, notes = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            values,
        )
    create_activity(user_id, company_id, "company_updated", "Client profile updated.")


def list_companies(user_id):
    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                """
                SELECT c.*,
                       (SELECT MAX(call_date) FROM call_notes WHERE company_id = c.id) AS last_call_date,
                       (SELECT meeting_date || ' ' || meeting_time FROM meetings
                        WHERE company_id = c.id AND status = 'Upcoming'
                        ORDER BY meeting_date ASC, meeting_time ASC LIMIT 1) AS next_meeting,
                       (SELECT close_probability FROM call_notes
                        WHERE company_id = c.id ORDER BY call_date DESC LIMIT 1) AS call_score
                FROM companies c
                WHERE c.user_id = ?
                ORDER BY c.updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        )


def get_company(user_id, company_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM companies WHERE id = ? AND user_id = ?",
            (company_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def create_meeting(user_id, company_id, data):
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO meetings (
                user_id, company_id, title, meeting_date, meeting_time, duration_minutes,
                meeting_type, status, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                company_id,
                data.get("title", "").strip(),
                data.get("meeting_date", "").strip(),
                data.get("meeting_time", "").strip(),
                int(data.get("duration_minutes") or 30),
                data.get("meeting_type", "Discovery"),
                data.get("status", "Upcoming"),
                data.get("notes", "").strip(),
                now,
                now,
            ),
        )
        meeting_id = cursor.lastrowid
    create_activity(user_id, company_id, "meeting_scheduled", f"Meeting scheduled: {data.get('title', '').strip()}.")
    return meeting_id


def list_meetings(user_id, company_id=None, upcoming_only=False):
    clauses = ["m.user_id = ?"]
    params = [user_id]
    if company_id:
        clauses.append("m.company_id = ?")
        params.append(company_id)
    if upcoming_only:
        clauses.append("m.status = 'Upcoming'")
    where = " AND ".join(clauses)

    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                f"""
                SELECT m.*, c.company_name, c.project_name
                FROM meetings m
                JOIN companies c ON c.id = m.company_id
                WHERE {where}
                ORDER BY m.meeting_date ASC, m.meeting_time ASC
                """,
                params,
            ).fetchall()
        )


def get_meeting(user_id, meeting_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT m.*, c.company_name, c.project_name, c.contact_name
            FROM meetings m
            JOIN companies c ON c.id = m.company_id
            WHERE m.id = ? AND m.user_id = ?
            """,
            (meeting_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def create_call_note(user_id, company_id, meeting_id, note):
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO call_notes (
                user_id, company_id, meeting_id, call_date, transcript, summary, objections,
                buying_signals, pain_points, action_items, follow_up_tasks,
                suggested_follow_up_email, call_score, close_probability, sentiment, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                company_id,
                meeting_id,
                note.get("call_date", now),
                note.get("transcript", ""),
                note.get("summary", ""),
                note.get("objections", ""),
                note.get("buying_signals", ""),
                note.get("pain_points", ""),
                note.get("action_items", ""),
                note.get("follow_up_tasks", ""),
                note.get("suggested_follow_up_email", ""),
                note.get("call_score", 0),
                note.get("close_probability", 0),
                note.get("sentiment", ""),
                now,
            ),
        )
        note_id = cursor.lastrowid
        if meeting_id:
            connection.execute(
                "UPDATE meetings SET status = 'Completed', updated_at = ? WHERE id = ? AND user_id = ?",
                (now, meeting_id, user_id),
            )
    create_activity(user_id, company_id, "call_completed", "AI call notes saved to this client.")
    return note_id


def list_call_notes(user_id, company_id=None, limit=None):
    clauses = ["n.user_id = ?"]
    params = [user_id]
    if company_id:
        clauses.append("n.company_id = ?")
        params.append(company_id)
    limit_sql = f" LIMIT {int(limit)}" if limit else ""

    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                f"""
                SELECT n.*, c.company_name, c.project_name
                FROM call_notes n
                JOIN companies c ON c.id = n.company_id
                WHERE {" AND ".join(clauses)}
                ORDER BY n.call_date DESC
                {limit_sql}
                """,
                params,
            ).fetchall()
        )


def get_call_note(user_id, note_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT n.*, c.company_name, c.project_name, c.contact_name
            FROM call_notes n
            JOIN companies c ON c.id = n.company_id
            WHERE n.id = ? AND n.user_id = ?
            """,
            (note_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def list_activity(user_id, company_id):
    with get_connection() as connection:
        return rows_to_dicts(
            connection.execute(
                """
                SELECT * FROM activity_timeline
                WHERE user_id = ? AND company_id = ?
                ORDER BY created_at DESC
                """,
                (user_id, company_id),
            ).fetchall()
        )


def dashboard_stats(user_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM companies WHERE user_id = ?) AS total_companies,
                (SELECT COUNT(*) FROM meetings WHERE user_id = ? AND status = 'Upcoming') AS upcoming_meetings,
                (SELECT COUNT(*) FROM call_notes WHERE user_id = ?) AS calls_completed,
                (SELECT COALESCE(ROUND(AVG(call_score)), 0) FROM call_notes WHERE user_id = ?) AS average_call_score,
                (SELECT COUNT(*) FROM companies WHERE user_id = ? AND status = 'Follow-up Needed') AS followups_due
            """,
            (user_id, user_id, user_id, user_id, user_id),
        ).fetchone()
        return dict(row)


def firebase_enabled():
    return os.getenv("DATABASE_PROVIDER", "sqlite").lower() in ("firebase", "firestore")


def firebase_client():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as error:
        raise RuntimeError("firebase-admin is required when DATABASE_PROVIDER=firebase.") from error

    try:
        firebase_admin.get_app()
    except ValueError:
        credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
        project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()

        options = {"projectId": project_id} if project_id else None
        if credentials_json:
            import json

            cred = credentials.Certificate(json.loads(credentials_json))
            firebase_admin.initialize_app(cred, options=options)
        elif credentials_path:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred, options=options)
        else:
            firebase_admin.initialize_app(options=options)

    return firestore.client()


def firebase_init_db():
    firebase_client()


def firebase_next_id(name):
    from firebase_admin import firestore

    db = firebase_client()
    counter_ref = db.collection("_metadata").document(f"{name}_counter")
    transaction = db.transaction()

    @firestore.transactional
    def increment(current_transaction):
        snapshot = counter_ref.get(transaction=current_transaction)
        current_value = snapshot.to_dict().get("value", 0) if snapshot.exists else 0
        next_value = int(current_value) + 1
        current_transaction.set(counter_ref, {"value": next_value}, merge=True)
        return next_value

    return increment(transaction)


def firebase_doc_to_dict(snapshot):
    if not snapshot.exists:
        return None
    data = snapshot.to_dict()
    data["id"] = int(data.get("id", snapshot.id))
    return data


def firebase_collection(name):
    return firebase_client().collection(name)


def firebase_docs(collection_name):
    return [firebase_doc_to_dict(doc) for doc in firebase_collection(collection_name).stream()]


def firebase_data_get(data, field, default=""):
    value = data.get(field, default)
    return value.strip() if isinstance(value, str) else value


def firebase_create_user(name, email, password):
    email = email.lower().strip()
    if firebase_find_user_by_email(email):
        raise ValueError("Email already registered.")

    user_id = firebase_next_id("users")
    user = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": utc_now(),
    }
    firebase_collection("users").document(str(user_id)).set(user)
    return user_id


def firebase_find_user_by_email(email):
    email = email.lower().strip()
    for doc in firebase_collection("users").where("email", "==", email).limit(1).stream():
        return firebase_doc_to_dict(doc)
    return None


def firebase_find_user_by_id(user_id):
    return firebase_doc_to_dict(firebase_collection("users").document(str(user_id)).get())


def firebase_verify_user(email, password):
    user = firebase_find_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return None
    return user


def firebase_create_activity(user_id, company_id, activity_type, description):
    activity_id = firebase_next_id("activity_timeline")
    firebase_collection("activity_timeline").document(str(activity_id)).set(
        {
            "id": activity_id,
            "user_id": int(user_id),
            "company_id": int(company_id),
            "activity_type": activity_type,
            "description": description,
            "created_at": utc_now(),
        }
    )


def firebase_create_company(user_id, data):
    now = utc_now()
    company_id = firebase_next_id("companies")
    company = {
        "id": company_id,
        "user_id": int(user_id),
        "company_name": firebase_data_get(data, "company_name"),
        "project_name": firebase_data_get(data, "project_name"),
        "contact_name": firebase_data_get(data, "contact_name"),
        "contact_email": firebase_data_get(data, "contact_email"),
        "contact_phone": firebase_data_get(data, "contact_phone"),
        "website": firebase_data_get(data, "website"),
        "deal_stage": firebase_data_get(data, "deal_stage") or "New Lead",
        "priority": firebase_data_get(data, "priority") or "Medium",
        "status": firebase_data_get(data, "status") or "Active",
        "product_or_service": firebase_data_get(data, "product_or_service"),
        "pain_points": firebase_data_get(data, "pain_points"),
        "notes": firebase_data_get(data, "notes"),
        "created_at": now,
        "updated_at": now,
    }
    firebase_collection("companies").document(str(company_id)).set(company)
    firebase_create_activity(user_id, company_id, "company_created", f"Company {company['company_name']} created.")
    return company_id


def firebase_update_company(user_id, company_id, data):
    company = {
        "company_name": firebase_data_get(data, "company_name"),
        "project_name": firebase_data_get(data, "project_name"),
        "contact_name": firebase_data_get(data, "contact_name"),
        "contact_email": firebase_data_get(data, "contact_email"),
        "contact_phone": firebase_data_get(data, "contact_phone"),
        "website": firebase_data_get(data, "website"),
        "deal_stage": firebase_data_get(data, "deal_stage") or "New Lead",
        "priority": firebase_data_get(data, "priority") or "Medium",
        "status": firebase_data_get(data, "status") or "Active",
        "product_or_service": firebase_data_get(data, "product_or_service"),
        "pain_points": firebase_data_get(data, "pain_points"),
        "notes": firebase_data_get(data, "notes"),
        "updated_at": utc_now(),
    }
    ref = firebase_collection("companies").document(str(company_id))
    existing = firebase_doc_to_dict(ref.get())
    if existing and int(existing["user_id"]) == int(user_id):
        ref.update(company)
        firebase_create_activity(user_id, company_id, "company_updated", "Client profile updated.")


def firebase_company_notes(user_id, company_id=None):
    notes = [note for note in firebase_docs("call_notes") if int(note["user_id"]) == int(user_id)]
    if company_id:
        notes = [note for note in notes if int(note["company_id"]) == int(company_id)]
    return notes


def firebase_company_meetings(user_id, company_id=None):
    meetings = [meeting for meeting in firebase_docs("meetings") if int(meeting["user_id"]) == int(user_id)]
    if company_id:
        meetings = [meeting for meeting in meetings if int(meeting["company_id"]) == int(company_id)]
    return meetings


def firebase_list_companies(user_id):
    companies = [company for company in firebase_docs("companies") if int(company["user_id"]) == int(user_id)]
    notes = firebase_company_notes(user_id)
    meetings = firebase_company_meetings(user_id)

    for company in companies:
        company_notes = [note for note in notes if int(note["company_id"]) == int(company["id"])]
        company_meetings = [
            meeting for meeting in meetings
            if int(meeting["company_id"]) == int(company["id"]) and meeting.get("status") == "Upcoming"
        ]
        latest_note = sorted(company_notes, key=lambda item: item.get("call_date", ""), reverse=True)[:1]
        next_meeting = sorted(company_meetings, key=lambda item: (item.get("meeting_date", ""), item.get("meeting_time", "")))[:1]
        company["last_call_date"] = latest_note[0].get("call_date") if latest_note else None
        company["call_score"] = latest_note[0].get("close_probability") if latest_note else None
        company["next_meeting"] = (
            f"{next_meeting[0].get('meeting_date', '')} {next_meeting[0].get('meeting_time', '')}"
            if next_meeting else None
        )

    return sorted(companies, key=lambda item: item.get("updated_at", ""), reverse=True)


def firebase_get_company(user_id, company_id):
    company = firebase_doc_to_dict(firebase_collection("companies").document(str(company_id)).get())
    if not company or int(company["user_id"]) != int(user_id):
        return None
    return company


def firebase_create_meeting(user_id, company_id, data):
    now = utc_now()
    meeting_id = firebase_next_id("meetings")
    meeting = {
        "id": meeting_id,
        "user_id": int(user_id),
        "company_id": int(company_id),
        "title": firebase_data_get(data, "title"),
        "meeting_date": firebase_data_get(data, "meeting_date"),
        "meeting_time": firebase_data_get(data, "meeting_time"),
        "duration_minutes": int(firebase_data_get(data, "duration_minutes") or 30),
        "meeting_type": firebase_data_get(data, "meeting_type") or "Discovery",
        "status": firebase_data_get(data, "status") or "Upcoming",
        "notes": firebase_data_get(data, "notes"),
        "created_at": now,
        "updated_at": now,
    }
    firebase_collection("meetings").document(str(meeting_id)).set(meeting)
    firebase_create_activity(user_id, company_id, "meeting_scheduled", f"Meeting scheduled: {meeting['title']}.")
    return meeting_id


def firebase_list_meetings(user_id, company_id=None, upcoming_only=False):
    meetings = firebase_company_meetings(user_id, company_id)
    if upcoming_only:
        meetings = [meeting for meeting in meetings if meeting.get("status") == "Upcoming"]

    for meeting in meetings:
        company = firebase_get_company(user_id, meeting["company_id"])
        if company:
            meeting["company_name"] = company.get("company_name")
            meeting["project_name"] = company.get("project_name")

    return sorted(meetings, key=lambda item: (item.get("meeting_date", ""), item.get("meeting_time", "")))


def firebase_get_meeting(user_id, meeting_id):
    meeting = firebase_doc_to_dict(firebase_collection("meetings").document(str(meeting_id)).get())
    if not meeting or int(meeting["user_id"]) != int(user_id):
        return None
    company = firebase_get_company(user_id, meeting["company_id"])
    if company:
        meeting["company_name"] = company.get("company_name")
        meeting["project_name"] = company.get("project_name")
        meeting["contact_name"] = company.get("contact_name")
    return meeting


def firebase_create_call_note(user_id, company_id, meeting_id, note):
    now = utc_now()
    note_id = firebase_next_id("call_notes")
    call_note = {
        "id": note_id,
        "user_id": int(user_id),
        "company_id": int(company_id),
        "meeting_id": int(meeting_id) if meeting_id else None,
        "call_date": note.get("call_date", now),
        "transcript": note.get("transcript", ""),
        "summary": note.get("summary", ""),
        "objections": note.get("objections", ""),
        "buying_signals": note.get("buying_signals", ""),
        "pain_points": note.get("pain_points", ""),
        "action_items": note.get("action_items", ""),
        "follow_up_tasks": note.get("follow_up_tasks", ""),
        "suggested_follow_up_email": note.get("suggested_follow_up_email", ""),
        "call_score": int(note.get("call_score") or 0),
        "close_probability": int(note.get("close_probability") or 0),
        "sentiment": note.get("sentiment", ""),
        "created_at": now,
    }
    firebase_collection("call_notes").document(str(note_id)).set(call_note)
    if meeting_id:
        meeting_ref = firebase_collection("meetings").document(str(meeting_id))
        meeting = firebase_doc_to_dict(meeting_ref.get())
        if meeting and int(meeting["user_id"]) == int(user_id):
            meeting_ref.update({"status": "Completed", "updated_at": now})
    firebase_create_activity(user_id, company_id, "call_completed", "AI call notes saved to this client.")
    return note_id


def firebase_list_call_notes(user_id, company_id=None, limit=None):
    notes = firebase_company_notes(user_id, company_id)
    for note in notes:
        company = firebase_get_company(user_id, note["company_id"])
        if company:
            note["company_name"] = company.get("company_name")
            note["project_name"] = company.get("project_name")
    notes = sorted(notes, key=lambda item: item.get("call_date", ""), reverse=True)
    return notes[: int(limit)] if limit else notes


def firebase_get_call_note(user_id, note_id):
    note = firebase_doc_to_dict(firebase_collection("call_notes").document(str(note_id)).get())
    if not note or int(note["user_id"]) != int(user_id):
        return None
    company = firebase_get_company(user_id, note["company_id"])
    if company:
        note["company_name"] = company.get("company_name")
        note["project_name"] = company.get("project_name")
        note["contact_name"] = company.get("contact_name")
    return note


def firebase_list_activity(user_id, company_id):
    activities = [
        activity for activity in firebase_docs("activity_timeline")
        if int(activity["user_id"]) == int(user_id) and int(activity["company_id"]) == int(company_id)
    ]
    return sorted(activities, key=lambda item: item.get("created_at", ""), reverse=True)


def firebase_dashboard_stats(user_id):
    companies = [company for company in firebase_docs("companies") if int(company["user_id"]) == int(user_id)]
    meetings = [meeting for meeting in firebase_docs("meetings") if int(meeting["user_id"]) == int(user_id)]
    notes = [note for note in firebase_docs("call_notes") if int(note["user_id"]) == int(user_id)]
    scores = [int(note.get("call_score") or 0) for note in notes]
    return {
        "total_companies": len(companies),
        "upcoming_meetings": len([meeting for meeting in meetings if meeting.get("status") == "Upcoming"]),
        "calls_completed": len(notes),
        "average_call_score": round(sum(scores) / len(scores)) if scores else 0,
        "followups_due": len([company for company in companies if company.get("status") == "Follow-up Needed"]),
    }


if firebase_enabled():
    init_db = firebase_init_db
    create_user = firebase_create_user
    find_user_by_email = firebase_find_user_by_email
    find_user_by_id = firebase_find_user_by_id
    verify_user = firebase_verify_user
    create_activity = firebase_create_activity
    create_company = firebase_create_company
    update_company = firebase_update_company
    list_companies = firebase_list_companies
    get_company = firebase_get_company
    create_meeting = firebase_create_meeting
    list_meetings = firebase_list_meetings
    get_meeting = firebase_get_meeting
    create_call_note = firebase_create_call_note
    list_call_notes = firebase_list_call_notes
    get_call_note = firebase_get_call_note
    list_activity = firebase_list_activity
    dashboard_stats = firebase_dashboard_stats
