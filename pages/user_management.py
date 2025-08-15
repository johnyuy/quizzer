import streamlit as st
from utility import *

def admin_panel():
    st.subheader("User Management")
    users = load_users()

    # Create new user
    st.write("### Create New User")
    new_username = st.text_input("New username", max_chars=20)
    new_password = st.text_input("New password", type="password", max_chars=20)
    new_role = st.radio("Role", ["admin", "student"], horizontal=True)

    if st.button("Create User"):
        if new_username in users:
            st.error("User already exists!")
        elif not new_username or not new_password:
            st.error("Username and password cannot be empty.")
        else:
            users[new_username] = {"password": new_password, "role": new_role}
            save_users(users)
            st.success(f"User '{new_username}' created successfully!")

    # Delete user
    st.write("### Delete User")
    delete_username = st.selectbox("Select user to delete", [u for u in users.keys() if u != "admin"])
    if st.button("Delete User"):
        if delete_username in users:
            del users[delete_username]
            save_users(users)
            st.success(f"User '{delete_username}' deleted successfully!")

    st.write("### Current Users")
    st.json(users)

if not check_credentials():  
    st.stop()

if st.session_state["role"] == "admin":
    admin_panel()
    get_side_bar()
else:
    st.switch_page("pages/unauthorized.py")