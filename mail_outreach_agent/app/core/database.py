import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS recipients (id INTEGER PRIMARY KEY, company TEXT, email TEXT, contact_name TEXT, category TEXT, city TEXT, comment TEXT, website TEXT, status TEXT)""",
    """CREATE TABLE IF NOT EXISTS campaigns (id INTEGER PRIMARY KEY, created_at TEXT, subject_template TEXT, body_template TEXT, attachment_path TEXT)""",
    """CREATE TABLE IF NOT EXISTS emails (id INTEGER PRIMARY KEY, campaign_id INTEGER, recipient_id INTEGER, subject TEXT, body TEXT, status TEXT, sent_at TEXT, error_message TEXT)""",
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


def insert_recipients(rows: Iterable[dict]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM recipients")
        conn.executemany(
            "INSERT INTO recipients(company,email,contact_name,category,city,comment,website,status) VALUES (?,?,?,?,?,?,?,?)",
            [(r["company"], r["email"], r["contact_name"], r["category"], r["city"], r["comment"], r["website"], r["status"]) for r in rows],
        )
