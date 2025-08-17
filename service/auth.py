import streamlit as st
import pandas as pd
import gspread
import hmac
from google.oauth2.service_account import Credentials

# Connect to Google Sheets
def get_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["sheets"]["users"])
    return sheet.sheet1  # first worksheet

def load_users():
    sheet = get_gsheet()
    records = sheet.get_all_records()
    return {row["username"]: {"password": row["password"], "role": row["role"]} for row in records}

def save_users(users):
    sheet = get_gsheet()
    data = [["username", "password", "role"]]  # header
    for u, info in users.items():
        data.append([u, info["password"], info["role"]])
    sheet.update("A1", data)

def delete_user(username):
    sheet = get_gsheet()
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):  # start=2 because row 1 is the header
        if row["username"] == username:
            sheet.delete_rows(idx)
            return True
    return False

def check_credentials():
    users = load_users()
    username = st.session_state["username"]
    password = st.session_state["password"]

    # Check root accounts
    if username in st.secrets["rootusers"]:
        stored_password = st.secrets["rootusers"][username]["password"]
        if hmac.compare_digest(
            str(password), 
            str(stored_password)
            ):
            st.session_state["credentials_correct"] = True
            st.session_state["role"] = st.secrets["rootusers"][username]["role"]
            st.session_state["username_logged"] = username
            del st.session_state["password"]
            return

    # Check gsheet users
    if username in users and hmac.compare_digest(
        str(password),
        str(users[username]["password"])
        ):
        st.session_state["credentials_correct"] = True
        st.session_state["role"] = users[username]["role"]
        st.session_state["username_logged"] = username
        del st.session_state["password"]
        return
    st.session_state["credentials_correct"] = False
    return False

def logout():
    """Logs out the current user by clearing session state."""
    for key in ["credentials_correct", "role", "username_logged", "password", "username"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
