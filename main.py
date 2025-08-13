import streamlit as st
from utility import check_credentials, get_side_bar


APP_NAME = "Quizzer"
VERSION = 0.1
BADGE = f"{APP_NAME}-v{VERSION}"

if not check_credentials():  
    st.stop()

with st.container():
    st.title(f'Welcome, {st.session_state["username_logged"]}!')
    st.badge(BADGE, color='blue')


if st.session_state["role"] == 'admin':

    st.markdown('''
            **As an admin, you can:**  
            &mdash;  Manage Users  
            &mdash;  Manage Documents  
            &mdash;  Manage Quizzes  
            &mdash;  Print Results
            ''')

elif st.session_state["role"] == 'student':
    st.markdown('''
            **As a student, you can:**  
            &mdash;  Query a topic  
            &mdash;  Take a quiz   
            &mdash;  Print Results
            ''')


get_side_bar()
