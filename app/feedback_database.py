import json
import os
from pathlib import Path
import sqlite3
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATABASE_PATH = Path(__file__).resolve().parent / "feedback.db"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def using_supabase():
    return bool(SUPABASE_URL and SUPABASE_KEY)


def supabase_request(method, path, payload=None, query=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if method == "POST":
        headers["Prefer"] = "return=minimal"

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase request failed ({error.code}): {detail}") from error


def initialize_database():
    if using_supabase():
        return

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS satisfaction_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL DEFAULT '',
                major TEXT NOT NULL,
                semester TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT '',
                recommended_courses TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_feedback(rating, comment, major, semester, keywords, recommended_courses):
    if using_supabase():
        supabase_request(
            "POST",
            "satisfaction_feedback",
            payload={
                "rating": rating,
                "comment": comment,
                "major": major,
                "semester": semester,
                "keywords": keywords,
                "recommended_courses": recommended_courses,
            },
        )
        return

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO satisfaction_feedback (
                rating, comment, major, semester, keywords, recommended_courses
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rating,
                comment,
                major,
                semester,
                keywords,
                recommended_courses,
            ),
        )
        connection.commit()


def get_feedback_summary():
    if using_supabase():
        rows = supabase_request(
            "GET",
            "satisfaction_feedback",
            query={"select": "rating"},
        ) or []
        ratings = [row["rating"] for row in rows]
        return (sum(ratings) / len(ratings), len(ratings)) if ratings else (None, 0)

    with sqlite3.connect(DATABASE_PATH) as connection:
        average_rating, total_reviews = connection.execute(
            """
            SELECT AVG(rating), COUNT(*)
            FROM satisfaction_feedback
            """
        ).fetchone()

    return average_rating, total_reviews
