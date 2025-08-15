import streamlit as st
from service.auth import check_credentials


APP_NAME = "Quizzer"
DATE = "2025.08"
st.header(APP_NAME)
st.badge(f"{DATE}", color='blue')

with st.form("Login", border=True):
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    submitted = st.form_submit_button("Login", use_container_width=True)
    if submitted:
        check_credentials()
        if "credentials_correct" in st.session_state:
            if not st.session_state["credentials_correct"]:
                st.error("😕 Username or password is incorrect, please try again.")
            else:
                print(f'{st.session_state["username"]} logged in')
                # st.switch_page("pages/homepage.py")
                st.rerun()