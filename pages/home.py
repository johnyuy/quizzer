import streamlit as st

st.header(f"Welcome, {str(st.session_state['username_logged']).title()}!")
st.caption(f"##### As {st.session_state["role"]}, you can..")
role = st.session_state.get("role", "")
if role == "admin":
    user_mgmt, doc_mgmt, quiz_mgmt = st.columns(3)
    with user_mgmt:
        with st.container(border=True, height=160, vertical_alignment='top'):
            st.write('###### Manage Users')
            st.page_link("pages/user-management/create_user.py", icon=":material/person_add:", width="stretch")
            st.page_link("pages/user-management/delete_user.py", icon=":material/person_remove:", width="stretch")
    with doc_mgmt:
        with st.container(border=True, height=160, vertical_alignment='top'):
            st.write('###### Manage Document')
            st.page_link("pages/doc-management/upload_doc.py", icon=":material/upload_file:", width="stretch")
            st.page_link("pages/doc-management/manage_doc.py", icon=":material/collections_bookmark:", width="stretch")
    with quiz_mgmt:
        with st.container(border=True, height=160, vertical_alignment='top'):
            st.write('###### Manage Quizzes')
            st.page_link("pages/quiz-management/generate_quiz.py", icon=":material/psychology:", width="stretch")
            st.page_link("pages/quiz-management/manage_quiz.py", icon=":material/task:", width="stretch")

elif role == "student":
    ask, practice, quiz, results = st.columns(4)
    with ask:
         with st.container(border=True, height=80, vertical_alignment='center'):
             st.page_link("pages/student/ask.py", icon=":material/auto_stories:", width="stretch")
    with practice:
         with st.container(border=True, height=80, vertical_alignment='center'):
             st.page_link("pages/student/practice.py", icon=":material/edit_note:", width="stretch")
    with quiz:
        with st.container(border=True, height=80, vertical_alignment='center'):
            st.page_link("pages/student/quiz.py", icon=":material/task:", width="stretch")
    with results:
        with st.container(border=True, height=80, vertical_alignment='center'):
            st.page_link("pages/student/result.py", icon=":material/leaderboard:", width="stretch")

with st.expander("Important Notice", expanded=True):
    st.caption("""IMPORTANT NOTICE: This web application is a prototype developed for educational purposes only.  
               The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions,
               especially those related to financial, legal, or healthcare matters.
               """)
    st.caption("""
               Furthermore, please be aware that the LLM may generate inaccurate or incorrect information.
               You assume full responsibility for how you use any generated output.
               """)
    st.caption("""
               Always consult with qualified professionals for accurate and personalized advice.
               """)
    