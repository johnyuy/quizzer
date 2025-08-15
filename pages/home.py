import streamlit as st

st.title("Quizzer")

role = st.session_state.get("role", "")
if role == "admin":
    user_mgmt, doc_mgmt = st.columns(2)
    with user_mgmt:
        with st.container(border=True, height=150, vertical_alignment='top'):
            st.write('###### User Management')
            st.page_link("pages/user-management/create_user.py", icon=":material/person_add:", width="stretch")
            st.page_link("pages/user-management/delete_user.py", icon=":material/person_remove:", width="stretch")
    with doc_mgmt:
        with st.container(border=True, height=150, vertical_alignment='top'):
            st.write('###### Document Management')
            st.page_link("pages/doc-management/upload_doc.py", icon=":material/upload_file:", width="stretch")
elif role == "student":
    ask, quiz = st.columns(2)
    with ask:
         with st.container(border=True, height=80, vertical_alignment='center'):
             st.page_link("pages/student/ask.py", icon=":material/auto_stories:", width="stretch")
    with quiz:
        with st.container(border=True, height=80, vertical_alignment='center'):
            st.page_link("pages/student/quiz.py", icon=":material/task:", width="stretch")
    