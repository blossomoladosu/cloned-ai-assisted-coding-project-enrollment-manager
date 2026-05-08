# Detailed Streamlit UI Implementation Plan for Student Enrollment Manager

## App Overview

This is a student-facing enrollment dashboard built on top of an existing layered backend. The app assumes the student is already logged in and uses Maya Patel (user_id="u100") as the simulated current user. The role "student" is stored in st.session_state.

## Assumptions: Do

- Use the existing service layer for all enrollment and unenrollment actions
- Preserve the layered backend architecture
- Use st.session_state to track: current page, selected class, current role, success/warning/error messages
- Keep all business logic inside the service layer
- Keep SQL isolated inside the database/store layer

## Assumptions: Do Not

- Do not build login, registration, password handling, account creation, or a new authentication system
- Do not move business logic into the Streamlit UI
- Do not place SQL inside the UI
- Do not bypass the service layer and directly access the database layer

## Backend Architecture

The backend consists of three layers:
- **CodeStore**: Handles all SQLite queries and updates
- **CodeService**: Contains business logic for enrollment operations
- **CodeDashboard**: Orchestrates operations and handles export behavior

The UI will only interact with the CodeService layer.

## App Structure

The app follows a two-page student flow:
- **Student Dashboard Page**: Main enrollment management interface
- **Selected Class Page**: Detailed view of a specific enrolled class

## Proposed Streamlit File Structure

```
streamlit_app.py              # Main Streamlit app entry point
pages/
├── __init__.py
├── dashboard.py              # Student Dashboard page implementation
└── selected_class.py         # Selected Class page implementation
services/
├── __init__.py
└── enrollment_service.py     # Service layer wrapper for UI calls
utils/
├── __init__.py
├── session_utils.py          # Session state management utilities
└── ui_components.py          # Reusable UI components
```

## Page Layout and UI Organization

### Student Dashboard Page Layout

**Header Section:**
- `st.title("Student Enrollment Dashboard")`
- `st.caption("Welcome, Maya Patel")`

**Enrolled Classes Section:**
- `st.container()` wrapper
- `st.subheader("Your Enrolled Classes")`
- `st.dataframe()` displaying enrolled courses with columns: Course ID, Course Name, Instructor, Enrolled At
- For each course row: `st.columns()` with "Go to Class" `st.button()` and "Unenroll" `st.button()`

**Enrollment Summary Section:**
- `st.container()` wrapper
- `st.subheader("Enrollment Summary")`
- `st.columns()` with `st.metric()` components for: Total Enrolled, Total Records, Unenrolled Count

**Enroll New Class Section:**
- `st.container()` wrapper
- `st.subheader("Enroll in a New Class")`
- `st.form()` containing:
  - `st.text_input()` for enrollment key
  - `st.form_submit_button("Enroll")`

**Messages Section:**
- `st.container()` wrapper
- Conditional display of `st.success()`, `st.warning()`, `st.error()` based on session state messages

**Layout Flow:**
- Use `st.divider()` between major sections
- Responsive layout with `st.columns()` for action buttons and metrics

### Selected Class Page Layout

**Header Section:**
- `st.title(course_name)`
- `st.button("← Back to Dashboard")` in top-right via `st.columns()`

**Class Information Section:**
- `st.container()` wrapper
- `st.subheader("Class Details")`
- `st.columns()` layout with:
  - Left column: Course ID, Course Name, Instructor
  - Right column: Enrollment Status, Enrolled At
- Use `st.info()` box for enrollment status display

**Messages Section:**
- `st.container()` wrapper
- Conditional display of messages (same as dashboard)

**Layout Flow:**
- Clean, centered layout with appropriate spacing
- Use `st.divider()` for section separation

## Routing Flow

Routing is controlled entirely through st.session_state:

1. **App Initialization** (in streamlit_app.py):
   - Initialize session state with defaults
   - Set `st.session_state.page = "dashboard"`
   - Set `st.session_state.user_id = "u100"`
   - Set `st.session_state.role = "student"`
   - Set `st.session_state.messages = []`

2. **Page Rendering Logic**:
   - Check `st.session_state.role` - if not "student", show error message
   - Based on `st.session_state.page`, render appropriate page:
     - "dashboard" → import and call dashboard.render()
     - "class" → import and call selected_class.render()

3. **Navigation Actions**:
   - "Go to Class" button: Set `st.session_state.page = "class"`, `st.session_state.selected_class = course_id`, call `st.rerun()`
   - "Back to Dashboard" button: Set `st.session_state.page = "dashboard"`, call `st.rerun()`

4. **Role Checking**:
   - At app start, verify `st.session_state.role == "student"`
   - If role is not "student", display `st.error("Access denied. Student role required.")` and stop rendering
   - This prevents non-student users from accessing the enrollment interface

## Session State Design

st.session_state structure:

```python
{
    "page": "dashboard" | "class",           # Current page identifier
    "user_id": "u100",                       # Current student user ID
    "role": "student",                       # User role (must be "student")
    "selected_class": "MISY350",             # Course ID for class page (set when navigating)
    "messages": [                            # List of feedback message dictionaries
        {
            "type": "success" | "warning" | "error",
            "text": "Message content"
        }
    ]
}
```

**Session State Management:**
- Use `session_utils.py` for helper functions to get/set session values safely
- Initialize defaults in `streamlit_app.py` on first run
- Clear messages after display to prevent persistence

## Selected-Class Navigation Flow

1. **From Dashboard**: User clicks "Go to Class" button for a specific course
2. **State Update**: Set `st.session_state.selected_class = course_id`
3. **Page Navigation**: Set `st.session_state.page = "class"`
4. **UI Refresh**: Call `st.rerun()` to render class page
5. **Data Retrieval**: Class page calls service layer to get course details using `selected_class`
6. **Back Navigation**: "Back to Dashboard" button resets `page = "dashboard"` and calls `st.rerun()`

## Feedback/Message Handling

**Message System:**
- Messages stored as list of dicts in `st.session_state.messages`
- Each message has `type` ("success", "warning", "error") and `text`
- Display logic in `ui_components.py` with helper functions

**Message Display:**
- Dashboard and class pages both render messages section
- Use `st.success()`, `st.warning()`, `st.error()` based on message type
- Clear messages after display to prevent showing stale messages

**Message Triggers:**
- Successful enrollment: Add success message
- Invalid enrollment key: Add error message
- Successful unenrollment: Add warning message (since it's soft unenroll)
- Failed operations: Add error message

## Backend Integration Points

**Service Layer Calls:**
- `enrollment_service.get_student_enrollments(user_id)` - Get enrolled courses
- `enrollment_service.enroll_with_key(user_id, email, enrollment_key)` - Enroll student
- `enrollment_service.soft_unenroll_student(user_id, course_id)` - Soft unenroll
- `enrollment_service.get_student_summary(user_id)` - Get enrollment counts
- `enrollment_service.get_course_details(course_id)` - Get course info for selected class

**Service Layer Wrapper:**
- `services/enrollment_service.py` provides clean interface for UI
- Wraps calls to CodeService methods
- Handles error responses and converts to UI-friendly format

## Data Flow Between UI, Service Layer, and Database Layer

1. **UI Action** (e.g., enroll button click):
   - UI collects input data (enrollment key)
   - UI calls `enrollment_service.enroll_with_key()`

2. **Service Layer Processing**:
   - CodeService validates enrollment key
   - CodeService calls CodeStore for database operations
   - CodeService returns success/failure with data

3. **UI Response**:
   - UI receives result from service call
   - UI updates session state (messages, potentially refresh data)
   - UI calls `st.rerun()` to refresh display

4. **Data Retrieval Flow**:
   - UI calls service for data (enrollments, summary)
   - Service layer orchestrates through CodeStore
   - UI receives data and renders it

## Rerun/Refresh Behavior After Actions

**After Enrollment:**
- Call service method
- If successful: Add success message, refresh enrolled courses data, `st.rerun()`
- If failed: Add error message, `st.rerun()`

**After Unenrollment:**
- Call service method
- Add warning message (soft unenroll confirmation)
- Refresh enrolled courses data
- `st.rerun()`

**After Navigation:**
- Update session state page/selected_class
- `st.rerun()` to render new page

**Data Refresh Pattern:**
- Store fetched data in session state to avoid repeated API calls
- Clear cached data when actions modify state
- Re-fetch data after enrollment/unenrollment actions

## Minimal Backend Adjustments

If needed for UI integration:

1. **Service Layer Methods**: Ensure CodeService has methods that return UI-friendly data structures (dicts/lists instead of raw database rows)

2. **Error Handling**: CodeService methods should return consistent error responses (e.g., None or specific error codes)

3. **Data Formatting**: CodeService could format dates and other data for display

4. **No Major Changes**: The plan assumes the backend already supports the required operations through CodeService

## Role Checking Implementation

**Role Verification:**
- Check `st.session_state.role == "student"` at app startup
- If role is not "student":
  - Display `st.error("Access denied. This application requires student role.")`
  - Do not render any enrollment UI
  - Optionally provide logout or role change mechanism (but since no auth, just show error)

**Role Storage:**
- Role is set to "student" for the simulated user
- In a real system, this would come from authentication/session management

## Selected-Class Data Retrieval

**Through Service Layer:**
- Never access database directly from UI
- Use `enrollment_service.get_course_details(course_id)` or similar CodeService method
- Service layer calls CodeStore to get course + enrollment data
- Returns formatted dict with course info, enrollment status, dates

**Data Structure:**
```python
{
    "course_id": "MISY350",
    "course_name": "Python for Business Analytics",
    "instructor": "Dr. Rivera",
    "enrollment_status": "enrolled",
    "enrolled_at": "2026-05-05 19:33:57"
}
```

This plan provides a complete roadmap for implementing the Streamlit UI while preserving the layered backend architecture and following Streamlit best practices.