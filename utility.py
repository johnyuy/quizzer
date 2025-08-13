import streamlit as st
import os
import inspect
import sys
import hmac
import gspread
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

def check_credentials():
    users = load_users()

    def credentials_entered():
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

    # Return True if already logged in
    if st.session_state.get("credentials_correct", False):
        return True

    with st.container():
        st.title(f'Quizzer App')

    # Ask for username and password
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password", on_change=credentials_entered)

    # Show error if wrong
    if "credentials_correct" in st.session_state and not st.session_state["credentials_correct"]:
        st.error("😕 Username or password incorrect")

    return False

def logout():
    """Logs out the current user by clearing session state."""
    for key in ["credentials_correct", "role", "username_logged", "password", "username"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()  # Refresh the app to show login screen


def get_filename(full_path=False, with_ext=False):
    try:
        # Inspect the call stack
        frame = inspect.stack()[1]  # 0 = this function, 1 = caller
        path = frame.filename
    except Exception:
        # fallback: try sys.argv[0] (Streamlit safe)
        if len(sys.argv) > 0:
            path = sys.argv[0]
        else:
            return None
    if full_path:
        path = os.path.abspath(path)
    else:
        path = os.path.basename(path)
    if not with_ext:
        path = os.path.splitext(path)[0]
    return path

def get_side_bar():
    try:
        # Inspect the call stack
        frame = inspect.stack()[1]  # 0 = this function, 1 = caller
        path = frame.filename
    except Exception:
        # fallback: try sys.argv[0] (Streamlit safe)
        if len(sys.argv) > 0:
            path = sys.argv[0]
        else:
            path = None

    path = os.path.basename(path)
    path = os.path.splitext(path)[0]
    st.set_page_config(initial_sidebar_state='expanded')
    with st.sidebar:
        if st.button("About", type='secondary' if path == 'main' else 'tertiary') :
            st.switch_page("main.py")
        if st.session_state["role"] == 'admin':
            if st.button("Manage Users", type='secondary' if path == 'user_management' else 'tertiary'):
                st.switch_page("pages/user_management.py")
            if st.button("Manage Documents", type='secondary' if path == 'doc_management' else 'tertiary'):
                st.switch_page("pages/doc_management.py")
            st.button("Manage Quizzes", type='tertiary', disabled=True)
            st.button("Print Results", type='tertiary', disabled=True)
        elif st.session_state["role"] == 'student':
            st.button("Query a Topic", type='tertiary', disabled=True)
            st.button("Take a Quiz", type='tertiary', disabled=True)
        if st.button("Logout", type='tertiary'):
            logout()
            check_credentials()