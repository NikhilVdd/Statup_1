import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_URL", str(BASE_DIR / "loading_mvp.sqlite3"))


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
