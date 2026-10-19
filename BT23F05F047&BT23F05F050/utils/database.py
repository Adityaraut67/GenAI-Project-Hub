import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "smartnotes.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL DEFAULT '',
                total_questions INTEGER NOT NULL DEFAULT 0,
                score INTEGER NOT NULL DEFAULT 0,
                percentage REAL NOT NULL DEFAULT 0,
                wrong_questions TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)


def init_document_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                file_hash TEXT PRIMARY KEY,
                document_name TEXT NOT NULL,
                document_text TEXT NOT NULL DEFAULT '',
                page_count INTEGER NOT NULL DEFAULT 0,
                pages_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)
        # Migrate databases created by the earlier version without losing data.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)").fetchall()}
        if "pages_json" not in columns:
            conn.execute("ALTER TABLE documents ADD COLUMN pages_json TEXT NOT NULL DEFAULT '[]'")
        if "created_at" not in columns:
            conn.execute("ALTER TABLE documents ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")


def save_document(file_hash, document_name, document_text, page_count, pages=None):
    pages_json = json.dumps(pages or [], ensure_ascii=False)
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO documents (file_hash, document_name, document_text, page_count, pages_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_hash) DO UPDATE SET
                document_name=excluded.document_name,
                document_text=excluded.document_text,
                page_count=excluded.page_count,
                pages_json=excluded.pages_json
        """, (file_hash, document_name, document_text, page_count, pages_json, now))


def get_documents(search_term=""):
    query = "SELECT file_hash, document_name, page_count, created_at FROM documents"
    params = ()
    if search_term.strip():
        query += " WHERE document_name LIKE ?"
        params = (f"%{search_term.strip()}%",)
    query += " ORDER BY created_at DESC, document_name COLLATE NOCASE"
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_document(file_hash):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    try:
        result["pages"] = json.loads(result.get("pages_json") or "[]")
    except (TypeError, json.JSONDecodeError):
        result["pages"] = []
    return result


def delete_document(file_hash):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE file_hash = ?", (file_hash,))
        return cursor.rowcount > 0


def save_attempt(document_name, total_questions, score, wrong_questions):
    wrong_json = json.dumps(wrong_questions or [], ensure_ascii=False)
    percentage = (float(score) / int(total_questions) * 100) if total_questions else 0.0
    created_at = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO quiz_attempts
                (document_name, total_questions, score, percentage, wrong_questions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (document_name, total_questions, score, percentage, wrong_json, created_at))
        return cursor.lastrowid


def get_attempts(limit=None):
    query = "SELECT * FROM quiz_attempts ORDER BY created_at DESC, id DESC"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (int(limit),)
    with get_connection() as conn:
        rows = [dict(row) for row in conn.execute(query, params).fetchall()]
    for row in rows:
        try:
            row["wrong_questions"] = json.loads(row.get("wrong_questions") or "[]")
        except (TypeError, json.JSONDecodeError):
            row["wrong_questions"] = []
    return rows


def get_weak_topics():
    counts = {}
    questions = {}
    for attempt in get_attempts():
        for wrong in attempt.get("wrong_questions", []):
            if not isinstance(wrong, dict):
                continue
            topic = str(wrong.get("topic") or "General").strip() or "General"
            question = str(wrong.get("question") or "").strip()
            counts[topic] = counts.get(topic, 0) + 1
            if question:
                questions.setdefault(topic, set()).add(question)
    return [
        {"topic": topic, "incorrect_attempts": count, "unique_questions": len(questions.get(topic, set()))}
        for topic, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
    ]


def get_weak_questions(limit=10):
    counts = {}
    topics = {}
    for attempt in get_attempts():
        for wrong in attempt.get("wrong_questions", []):
            if not isinstance(wrong, dict):
                continue
            question = str(wrong.get("question") or "").strip()
            if not question:
                continue
            counts[question] = counts.get(question, 0) + 1
            topics[question] = str(wrong.get("topic") or "General")
    return [
        {"question": question, "topic": topics[question], "wrong_count": count}
        for question, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))[:limit]
    ]


def clear_history():
    with get_connection() as conn:
        conn.execute("DELETE FROM quiz_attempts")
