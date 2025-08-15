import streamlit as st
import pandas as pd
from service.auth import *


st.header("Delete User")
st.write("")

users = load_users()
self_username = st.session_state["username_logged"]
print(self_username)


with st.form("Delete User", border=False):
    
    delete_username = st.selectbox(
        "Select user:", 
        [u for u in users.keys() if u != "admin" and u != self_username],
        index=None
    )

    submitted = st.form_submit_button(
        "Delete User", 
        use_container_width=True,
        type="primary"
    )

    deleted_user = st.session_state.get("deleted_user", "")
    if deleted_user != "":
        st.success(f"User '{deleted_user}' deleted successfully.")
        st.session_state["deleted_user"] = ""
    
    if submitted:
        with st.spinner('Deleting user...'):
            if delete_user(delete_username):
                st.session_state["deleted_user"] = delete_username
                st.rerun()


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

