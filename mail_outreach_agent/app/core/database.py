import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS recipients (id INTEGER PRIMARY KEY, company TEXT, email TEXT, contact_name TEXT, category TEXT, city TEXT, comment TEXT, website TEXT, status TEXT)""",
    """CREATE TABLE IF NOT EXISTS campaigns (id INTEGER PRIMARY KEY, created_at TEXT, subject_template TEXT, body_template TEXT, attachment_path TEXT)""",
    """CREATE TABLE IF NOT EXISTS emails (id INTEGER PRIMARY KEY, campaign_id INTEGER, recipient_id INTEGER, company TEXT, email TEXT, subject TEXT, body TEXT, status TEXT, sent_at TEXT, error_message TEXT)""",
    """CREATE TABLE IF NOT EXISTS send_logs (id INTEGER PRIMARY KEY, email_id INTEGER, created_at TEXT, level TEXT, message TEXT)""",
    """CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""",
]


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        for sql in SCHEMA:
            conn.execute(sql)


def replace_emails(rows: Iterable[dict]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM emails")
        conn.executemany(
            "INSERT INTO emails(company,email,subject,body,status,sent_at,error_message) VALUES (?,?,?,?,?,?,?)",
            [(r.get("company", ""), r.get("email", ""), r.get("subject", ""), r.get("body", ""), r.get("send_status", "pending"), r.get("sent_at", ""), r.get("error_message", "")) for r in rows],
        )


def update_email_status(email: str, status: str, error_message: str = "", sent_at: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE emails SET status=?, error_message=?, sent_at=? WHERE email=?",
            (status, error_message, sent_at, email),
        )


def add_send_log(level: str, message: str, email: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO send_logs(email_id, created_at, level, message) VALUES ((SELECT id FROM emails WHERE email=? LIMIT 1), datetime('now'), ?, ?)",
            (email, level, message),
        )
