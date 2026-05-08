"""
Streamlit entry point for the student enrollment manager.

This app uses the existing layered backend:
- CodeStore for SQLite operations
- CodeService for enrollment business logic
- CodeDashboard for orchestration and export behavior
"""

from __future__ import annotations

import streamlit as st

from dashboard import CodeDashboard
from service import CodeService


def initialize_app() -> None:
    CodeDashboard.initialize_database()
    init_session_state()


def init_session_state() -> None:
    st.session_state.setdefault("page", "dashboard")
    st.session_state.setdefault("user_id", CodeDashboard.CURRENT_STUDENT["user_id"])
    st.session_state.setdefault("role", "student")
    st.session_state.setdefault("selected_class", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("form_enrollment_key", "")


def add_message(message_type: str, text: str) -> None:
    st.session_state.messages.append({"type": message_type, "text": text})


def clear_messages() -> None:
    st.session_state.messages = []


def render_messages() -> None:
    for message in st.session_state.messages:
        if message["type"] == "success":
            st.success(message["text"])
        elif message["type"] == "warning":
            st.warning(message["text"])
        else:
            st.error(message["text"])
    clear_messages()


def navigate_to_dashboard() -> None:
    st.session_state.page = "dashboard"
    st.session_state.selected_class = None


def navigate_to_class(course_id: str) -> None:
    st.session_state.page = "class"
    st.session_state.selected_class = course_id


def update_dashboard() -> None:
    user_id = st.session_state.user_id
    student = CodeDashboard.CURRENT_STUDENT
    st.title("Student Enrollment Dashboard")
    st.caption(f"Welcome, {student['name']}")

    if st.button("Export Database Snapshot"):
        CodeDashboard.export_database_snapshot()
        add_message("success", "Database snapshot exported to student_enrollment_snapshot.json")

    render_messages()

    st.divider()

    with st.container():
        st.subheader("Your Enrolled Classes")
        enrollments = CodeService.get_student_enrollments(user_id)
        if not enrollments:
            st.info("You are not enrolled in any classes yet.")
        else:
            for record in enrollments:
                course_columns = st.columns([3, 1, 1])
                course_columns[0].markdown(
                    f"**{record['course_id']} — {record['course_name']}**\n"
                    f"Instructor: {record['instructor']}\n"
                    f"Enrolled at: {record['enrolled_at']}"
                )
                course_columns[1].button(
                    "Go to Class",
                    key=f"go-{record['course_id']}",
                    on_click=navigate_to_class,
                    args=(record["course_id"],),
                )
                course_columns[2].button(
                    "Unenroll",
                    key=f"unenroll-{record['course_id']}",
                    on_click=soft_unenroll_handler,
                    args=(user_id, record["course_id"]),
                )

    st.divider()

    with st.container():
        st.subheader("Enrollment Summary")
        summary = CodeService.get_student_summary(user_id)
        summary_columns = st.columns(3)
        summary_columns[0].metric("Total Records", summary.get("total_records", 0))
        summary_columns[1].metric("Currently Enrolled", summary.get("enrolled", 0))
        summary_columns[2].metric("Total Unenrolled", summary.get("unenrolled", 0))

    st.divider()

    with st.container():
        st.subheader("Enroll in a New Class")
        with st.form("enroll_form"):
            st.text_input("Enrollment Key", key="form_enrollment_key")
            submitted = st.form_submit_button("Enroll")
            if submitted:
                enroll_handler(user_id, student["email"], st.session_state.form_enrollment_key)

        if st.session_state.form_enrollment_key:
            st.info(
                "Need a valid key? Try one of the seeded course keys below."
            )
            keys = CodeService.get_available_course_keys()
            st.table(
                [
                    {
                        "Course ID": item["course_id"],
                        "Course Name": item["course_name"],
                        "Instructor": item["instructor"],
                        "Enrollment Key": item["enrollment_key"],
                    }
                    for item in keys
                ]
            )


def render_selected_class() -> None:
    course_id = st.session_state.selected_class
    user_id = st.session_state.user_id
    details = CodeService.get_course_details(course_id, user_id)

    if not details:
        st.error("Selected course was not found.")
        if st.button("Back to Dashboard"):
            navigate_to_dashboard()
        return

    st.title(details["course_name"])
    back_col, _, _ = st.columns([1, 3, 1])
    if back_col.button("← Back to Dashboard"):
        navigate_to_dashboard()

    render_messages()

    with st.container():
        st.subheader("Class Details")
        info_columns = st.columns(2)
        info_columns[0].markdown(
            f"**Course ID:** {details['course_id']}  \n"
            f"**Instructor:** {details['instructor']}"
        )
        info_columns[1].markdown(
            f"**Status:** {details['enrollment_status'].title()}  \n"
            f"**Enrolled At:** {details['enrolled_at'] or 'N/A'}"
        )

    st.divider()

    if details["enrollment_status"] == "enrolled":
        if st.button("Unenroll from this class"):
            if CodeService.soft_unenroll_student(user_id, course_id):
                add_message("warning", f"You have been unenrolled from {details['course_id']}.")
                navigate_to_dashboard()
            else:
                add_message("error", "Unable to unenroll from this class.")
                st.experimental_rerun()


def enroll_handler(user_id: str, email: str, enrollment_key: str) -> None:
    if not enrollment_key:
        add_message("error", "Please enter an enrollment key.")
        return

    enrollment = CodeService.enroll_with_key(user_id, email, enrollment_key)
    if enrollment:
        add_message("success", f"Enrolled successfully in {enrollment['course_id']}.")
        st.session_state.form_enrollment_key = ""
    else:
        add_message("error", "Invalid enrollment key or enrollment failed.")


def soft_unenroll_handler(user_id: str, course_id: str) -> None:
    if CodeService.soft_unenroll_student(user_id, course_id):
        add_message("warning", f"You have been unenrolled from {course_id}.")
    else:
        add_message("error", "Unable to unenroll from this class.")


def main() -> None:
    initialize_app()
    if st.session_state.role != "student":
        st.error("Access denied. Student role required.")
        return

    if st.session_state.page == "dashboard":
        update_dashboard()
    else:
        render_selected_class()


if __name__ == "__main__":
    main()
