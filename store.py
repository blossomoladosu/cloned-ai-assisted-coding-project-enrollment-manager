"""
CodeStore: Database layer for enrollment operations.

Handles all SQLite queries and updates. No business logic here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional


DB_PATH = Path(__file__).with_name("student_enrollment_practice.db")


class CodeStore:
    """Database operations for enrollment system."""

    @staticmethod
    def connect() -> sqlite3.Connection:
        """Open a database connection."""
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def create_tables() -> None:
        """Create the courses and enrollments tables."""
        with CodeStore.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS courses (
                    course_id TEXT PRIMARY KEY,
                    course_name TEXT NOT NULL,
                    instructor TEXT NOT NULL,
                    enrollment_key TEXT NOT NULL UNIQUE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS enrollments (
                    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'enrolled',
                    enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, course_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )
                """
            )

    @staticmethod
    def seed_sample_data() -> None:
        """Seed courses, enrollment keys, and sample enrollment records."""
        with CodeStore.connect() as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO courses (
                    course_id, course_name, instructor, enrollment_key
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    ("MISY350", "Python for Business Analytics", "Dr. Rivera", "MISY350-SPRING"),
                    ("DATA210", "Data Storytelling", "Prof. Morgan", "DATA210-SPRING"),
                    ("WEB220", "Web Apps With Streamlit", "Dr. Chen", "WEB220-SPRING"),
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO enrollments (user_id, email, course_id, status)
                VALUES (?, ?, ?, ?)
                """,
                [
                    ("u100", "maya.patel@example.edu", "MISY350", "enrolled"),
                    ("u100", "maya.patel@example.edu", "DATA210", "unenrolled"),
                    ("u101", "alex@example.edu", "MISY350", "enrolled"),
                    ("u102", "blair@example.edu", "WEB220", "enrolled"),
                ],
            )

    @staticmethod
    def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        """Convert SQLite rows into dictionaries."""
        return [dict(row) for row in rows]

    @staticmethod
    def get_available_course_keys() -> list[dict[str, Any]]:
        """Return the course keys for reference."""
        with CodeStore.connect() as connection:
            rows = connection.execute(
                """
                SELECT course_id, course_name, instructor, enrollment_key
                FROM courses
                ORDER BY course_id
                """
            ).fetchall()
        return CodeStore.rows_to_dicts(rows)

    @staticmethod
    def get_course_by_key(enrollment_key: str) -> Optional[dict[str, Any]]:
        """Find a course by its enrollment key."""
        if not enrollment_key:
            return None

        with CodeStore.connect() as connection:
            row = connection.execute(
                """
                SELECT course_id, course_name, instructor, enrollment_key
                FROM courses
                WHERE enrollment_key = ?
                """,
                (enrollment_key.strip().upper(),),
            ).fetchone()

        return dict(row) if row else None

    @staticmethod
    def get_student_enrollments(user_id: str) -> list[dict[str, Any]]:
        """Return the classes where the student is currently enrolled."""
        if not user_id:
            return []

        with CodeStore.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.enrollment_id,
                    e.user_id,
                    e.email,
                    e.course_id,
                    c.course_name,
                    c.instructor,
                    e.status,
                    e.enrolled_at
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                WHERE e.user_id = ? AND e.status = ?
                ORDER BY c.course_id
                """,
                (user_id, "enrolled"),
            ).fetchall()

        return CodeStore.rows_to_dicts(rows)

    @staticmethod
    def get_student_enrollment_history(user_id: str) -> list[dict[str, Any]]:
        """Return all enrollment records for one student."""
        if not user_id:
            return []

        with CodeStore.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.enrollment_id,
                    e.user_id,
                    e.email,
                    e.course_id,
                    c.course_name,
                    c.instructor,
                    e.status,
                    e.enrolled_at
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                WHERE e.user_id = ?
                ORDER BY c.course_id
                """,
                (user_id,),
            ).fetchall()

        return CodeStore.rows_to_dicts(rows)

    @staticmethod
    def get_student_course_record(user_id: str, course_id: str) -> Optional[dict[str, Any]]:
        """Return one student's enrollment record for one course."""
        if not user_id or not course_id:
            return None

        with CodeStore.connect() as connection:
            row = connection.execute(
                """
                SELECT enrollment_id, user_id, email, course_id, status, enrolled_at
                FROM enrollments
                WHERE user_id = ? AND course_id = ?
                """,
                (user_id, course_id),
            ).fetchone()

        return dict(row) if row else None

    @staticmethod
    def enroll_with_key(user_id: str, email: str, course_id: str) -> Optional[dict[str, Any]]:
        """Enroll or reactivate a student in a course."""
        if not user_id or not email or "@" not in email or not course_id:
            return None

        with CodeStore.connect() as connection:
            connection.execute(
                """
                INSERT INTO enrollments (user_id, email, course_id, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, course_id)
                DO UPDATE SET
                    email = excluded.email,
                    status = excluded.status,
                    enrolled_at = CURRENT_TIMESTAMP
                """,
                (user_id, email, course_id, "enrolled"),
            )

        return CodeStore.get_student_course_record(user_id, course_id)

    @staticmethod
    def soft_unenroll_student(user_id: str, course_id: str) -> bool:
        """Soft-unenroll one student by changing status."""
        if not user_id or not course_id:
            return False

        with CodeStore.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE enrollments
                SET status = ?
                WHERE user_id = ? AND course_id = ?
                """,
                ("unenrolled", user_id, course_id),
            )

        return cursor.rowcount > 0

    @staticmethod
    def get_all_enrollment_records() -> list[dict[str, Any]]:
        """Return every enrollment record for export."""
        with CodeStore.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.enrollment_id,
                    e.user_id,
                    e.email,
                    e.course_id,
                    c.course_name,
                    c.instructor,
                    e.status,
                    e.enrolled_at
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                ORDER BY e.user_id, e.course_id
                """
            ).fetchall()

        return CodeStore.rows_to_dicts(rows)