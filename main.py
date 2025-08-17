import streamlit as st
import warnings
from service.auth import logout

from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

st.set_page_config(layout="centered")

login_page = st.Page(
    page="pages/login.py",
    title="Login",
    icon=":material/login:"
    )

home_page = st.Page(
    page="pages/home.py",
    title="Home",
    icon=":material/home:",
    default=True
    )

about_page = st.Page(
    page="pages/about_us.py",
    title="About",
    icon=":material/info:"
    )

methodology_page = st.Page(
    page="pages/methodology.py",
    title="Methodology",
    icon=":material/thumb_up:"
    )

create_user = st.Page(
    page="pages/user-management/create_user.py",
    title="Create User",
    icon=":material/person_add:"
    )

delete_user = st.Page(
    page="pages/user-management/delete_user.py",
    title="Delete User",
    icon=":material/person_remove:"
    )

upload_doc_page = st.Page(
    page="pages/doc-management/upload_doc.py",
    title="Upload Document",
    icon=":material/upload_file:"
    )

manage_doc_page = st.Page(
    page="pages/doc-management/manage_doc.py",
    title="Documents",
    icon=":material/collections_bookmark:"
    )

generate_quiz_page = st.Page(
    page="pages/quiz-management/generate_quiz.py",
    title="Generate Quiz",
    icon=":material/psychology:"
    )

manage_quiz_page = st.Page(
    page="pages/quiz-management/manage_quiz.py",
    title="Quizzes",
    icon=":material/task:"
    )

ask_page = st.Page(
    page="pages/student/ask.py",
    title="Learn",
    icon=":material/auto_stories:"
    )

practice_page = st.Page(
    page="pages/student/practice.py",
    title="Practice",
    icon=":material/edit_note:"
    )

quiz_page = st.Page(
    page="pages/student/quiz.py",
    title="Quiz",
    icon=":material/assignment:"
    )

result_page = st.Page(
    page="pages/student/result.py",
    title="Results",
    icon=":material/leaderboard:"
    )

# Grouping menu items
admin_pages = {
    "Quizzer": [home_page, about_page, methodology_page],
    "User Management": [create_user, delete_user],
    "Document Management": [upload_doc_page, manage_doc_page],
    "Quiz Management": [generate_quiz_page, manage_quiz_page]
}

student_pages = [home_page, ask_page, practice_page, quiz_page, result_page, about_page, methodology_page]

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

logged_in = st.session_state.get("credentials_correct", False)
role = st.session_state.get("role", "")

if logged_in:
    if role == "admin":
        pg = st.navigation(admin_pages, position="sidebar", expanded=True)
    elif role == "student":
        pg = st.navigation(student_pages, position="sidebar", expanded=True)
    else:
        logout()
        st.rerun()
    with st.sidebar:
        if st.button("Logout", icon=":material/logout:"):
            logout()
            st.rerun()
else:
    pg = st.navigation(
        [login_page, about_page, methodology_page]
    )

pg.run()