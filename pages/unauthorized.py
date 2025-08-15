import streamlit as st

def unauthorized_page():
    st.error("🚫 Unauthorized Access")
    st.write("You do not have permission to view this page.")
    if st.button("🔙 Back to Home"):
        st.switch_page("main.py")

unauthorized_page()