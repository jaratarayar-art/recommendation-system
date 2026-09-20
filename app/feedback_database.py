from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parent / "feedback.db"


def initialize_database():
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
    with sqlite3.connect(DATABASE_PATH) as connection:
        average_rating, total_reviews = connection.execute(
            """
            SELECT AVG(rating), COUNT(*)
            FROM satisfaction_feedback
            """
        ).fetchone()

    return average_rating, total_reviews
