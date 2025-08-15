import streamlit as st
from service.auth import check_credentials


logged_in = st.session_state.get("credentials_correct", False)
if not logged_in:
    with st.container(horizontal=True, vertical_alignment='center'):
        st.info("You are not logged in.")
        with st.container(width=100):
            st.page_link("pages/login.py", icon=":material/login:", use_container_width=True)

st.header("About Us")
st.write("here is some text")

