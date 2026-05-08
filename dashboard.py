"""
CodeDashboard: Orchestration and export layer for enrollment operations.

Handles high-level operations and data export functionality.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from service import CodeService
from store import CodeStore


class CodeDashboard:
    """Orchestration and export operations."""

    CURRENT_STUDENT = {
        "user_id": "u100",
        "name": "Maya Patel",
        "email": "maya.patel@example.edu",
    }

    @staticmethod
    def initialize_database() -> None:
        """Initialize database with tables and seed data."""
        CodeStore.create_tables()
        CodeStore.seed_sample_data()

    @staticmethod
    def export_database_snapshot(path: Path = Path("student_enrollment_snapshot.json")) -> None:
        """Write seeded database content to JSON for inspection."""
        snapshot = {
            "current_student": CodeDashboard.CURRENT_STUDENT,
            "available_course_keys": CodeStore.get_available_course_keys(),
            "enrollment_table": CodeStore.get_all_enrollment_records(),
        }
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    @staticmethod
    def get_dashboard_data(user_id: str) -> dict[str, Any]:
        """Get all data needed for the student dashboard."""
        return {
            "student": CodeDashboard.CURRENT_STUDENT,
            "enrollments": CodeService.get_student_enrollments(user_id),
            "summary": CodeService.get_student_summary(user_id),
        }