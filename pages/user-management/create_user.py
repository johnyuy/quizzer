import streamlit as st
from service.auth import *


st.header("Create User")
st.write("")

users = load_users()

with st.form("Create User", border=False):
    username = st.text_input("Username", max_chars=20,)
    password = st.text_input("Password", type="password", autocomplete="off", max_chars=20)
    role = st.radio("Role", ["student", "admin"], horizontal=True)
    submitted = st.form_submit_button("Create User", use_container_width=True, type="primary")
    if submitted:
        if username in users:
            st.error("User already exists!")
        elif username == "admin":
            st.error("Action forbidden.")
        elif not username or not password:
            st.error("Username and password cannot be empty.")
        elif len(password) < 6:
            st.error("Password cannot be shorter than 6 characters.")
        else:
            with st.spinner("Creating user..."):
                users[username] = {"password": password, "role": role}
                save_users(users)
                st.success(f"User '{username}' created successfully.")

    st.divider()
    st.write('#### List of Users')
    users_list = [{"Role": info["role"], "Name": name } for name, info in users.items()]
    users_df = pd.DataFrame(users_list)
    st.data_editor(
        users_df,
        column_config={
            "Role" : st.column_config.Column(width="small"),
            "Name" : st.column_config.Column(width="large")
        },
        hide_index=True, 
        disabled=True)