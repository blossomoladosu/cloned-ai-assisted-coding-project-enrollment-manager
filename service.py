"""
CodeService: Business logic layer for enrollment operations.

Handles enrollment logic, validation, summaries, and unenrollment behavior.
Calls CodeStore for database operations.
"""

from __future__ import annotations

from typing import Any, Optional

from store import CodeStore


class CodeService:
    """Business logic for enrollment operations."""

    STATUS_ENROLLED = "enrolled"
    STATUS_UNENROLLED = "unenrolled"

    @staticmethod
    def get_student_enrollments(user_id: str) -> list[dict[str, Any]]:
        """Return the classes where the student is currently enrolled."""
        return CodeStore.get_student_enrollments(user_id)

    @staticmethod
    def get_student_summary(user_id: str) -> dict[str, int]:
        """Return summary counts for one student."""
        summary = {
            "total_records": 0,
            "enrolled": 0,
            "unenrolled": 0,
        }

        for record in CodeStore.get_student_enrollment_history(user_id):
            summary["total_records"] += 1
            status = record["status"]
            if status in summary:
                summary[status] += 1

        return summary

    @staticmethod
    def enroll_with_key(user_id: str, email: str, enrollment_key: str) -> Optional[dict[str, Any]]:
        """Enroll or reactivate a student using a course enrollment key."""
        if not user_id or not email or "@" not in email or not enrollment_key:
            return None

        course = CodeStore.get_course_by_key(enrollment_key)
        if not course:
            return None

        return CodeStore.enroll_with_key(user_id, email, course["course_id"])

    @staticmethod
    def soft_unenroll_student(user_id: str, course_id: str) -> bool:
        """Soft-unenroll one student by changing status."""
        return CodeStore.soft_unenroll_student(user_id, course_id)

    @staticmethod
    def get_course_details(course_id: str, user_id: str) -> Optional[dict[str, Any]]:
        """Get course details with enrollment status for a specific user."""
        if not course_id or not user_id:
            return None

        # Get course info
        courses = CodeStore.get_available_course_keys()
        course = next((c for c in courses if c["course_id"] == course_id), None)
        if not course:
            return None

        # Get enrollment record
        enrollment = CodeStore.get_student_course_record(user_id, course_id)

        return {
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "instructor": course["instructor"],
            "enrollment_status": enrollment["status"] if enrollment else "not enrolled",
            "enrolled_at": enrollment["enrolled_at"] if enrollment else None,
        }

    @staticmethod
    def get_available_course_keys() -> list[dict[str, Any]]:
        """Return available enrollment keys for reference."""
        return CodeStore.get_available_course_keys()