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
TOPIC_COLUMNS = [f"topic_{index}" for index in range(1, 9)]


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
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL DEFAULT '',
                major TEXT NOT NULL,
                semester TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT '',
                recommended_courses TEXT NOT NULL DEFAULT '',
                topic_1 INTEGER NOT NULL DEFAULT 0 CHECK (topic_1 BETWEEN 0 AND 5),
                topic_2 INTEGER NOT NULL DEFAULT 0 CHECK (topic_2 BETWEEN 0 AND 5),
                topic_3 INTEGER NOT NULL DEFAULT 0 CHECK (topic_3 BETWEEN 0 AND 5),
                topic_4 INTEGER NOT NULL DEFAULT 0 CHECK (topic_4 BETWEEN 0 AND 5),
                topic_5 INTEGER NOT NULL DEFAULT 0 CHECK (topic_5 BETWEEN 0 AND 5),
                topic_6 INTEGER NOT NULL DEFAULT 0 CHECK (topic_6 BETWEEN 0 AND 5),
                topic_7 INTEGER NOT NULL DEFAULT 0 CHECK (topic_7 BETWEEN 0 AND 5),
                topic_8 INTEGER NOT NULL DEFAULT 0 CHECK (topic_8 BETWEEN 0 AND 5),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        existing_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(satisfaction_feedback)")
        }
        for column in TOPIC_COLUMNS:
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE satisfaction_feedback ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0"
                )
        connection.commit()


def save_feedback(topic_ratings, comment, major, semester, keywords, recommended_courses):
    overall_rating = round(sum(topic_ratings) / len(topic_ratings))

    if using_supabase():
        payload = {
            "rating": overall_rating,
            "comment": comment,
            "major": major,
            "semester": semester,
            "keywords": keywords,
            "recommended_courses": recommended_courses,
        }
        payload.update(dict(zip(TOPIC_COLUMNS, topic_ratings)))
        supabase_request(
            "POST",
            "satisfaction_feedback",
            payload=payload,
        )
        return

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO satisfaction_feedback (
                rating, comment, major, semester, keywords, recommended_courses,
                topic_1, topic_2, topic_3, topic_4, topic_5, topic_6, topic_7, topic_8
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                overall_rating,
                comment,
                major,
                semester,
                keywords,
                recommended_courses,
                *topic_ratings,
            ),
        )
        connection.commit()


def get_feedback_summary():
    if using_supabase():
        rows = supabase_request(
            "GET",
            "satisfaction_feedback",
            query={"select": "rating," + ",".join(TOPIC_COLUMNS)},
        ) or []
    else:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row
            rows = [
                dict(row)
                for row in connection.execute(
                    "SELECT rating, " + ", ".join(TOPIC_COLUMNS) + " FROM satisfaction_feedback"
                ).fetchall()
            ]

    topic_averages = []
    for column in TOPIC_COLUMNS:
        scores = [row.get(column) or 0 for row in rows if row.get(column)]
        topic_averages.append(sum(scores) / len(scores) if scores else None)

    review_scores = []
    for row in rows:
        topic_scores = [row.get(column) or 0 for column in TOPIC_COLUMNS]
        if any(topic_scores):
            review_scores.append(sum(topic_scores) / len([score for score in topic_scores if score]))
        elif row.get("rating") is not None:
            review_scores.append(row["rating"])

    average_rating = sum(review_scores) / len(review_scores) if review_scores else None
    return average_rating, len(rows), topic_averages
