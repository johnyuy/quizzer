import streamlit as st
from service.auth import logout

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

quiz_page = st.Page(
    page="pages/student/quiz.py",
    title="Quiz",
    icon=":material/task:"
    )

quizzer_page = st.Page(
    page="pages/student/quizzer.py",
    title="Take Quiz",
    icon=":material/task:"
    )


# Grouping menu items
admin_pages = {
    "Quizzer": [home_page, about_page],
    "User Management": [create_user, delete_user],
    "Document Management": [upload_doc_page, manage_doc_page],
    "Quiz Management": [generate_quiz_page, manage_quiz_page]
}

student_pages = [home_page, ask_page, quiz_page, quizzer_page, about_page]


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
        [login_page, about_page]
    )

pg.run()