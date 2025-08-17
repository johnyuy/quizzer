import streamlit as st
import gspread
import uuid
from google.oauth2.service_account import Credentials

def get_selected_document_label(doc):
    return f"{doc['filename']} (Uploaded: {doc['upload_timestamp']})"

def get_document_index(doc, docs):
    target = doc["point_id"]
    return next((i for i, p in enumerate(docs) if p['point_id'] == target), 0)

@st.cache_resource(ttl=15)
def get_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["sheets"]["quizzes"])
    return sheet.sheet1  # first worksheet

@st.cache_data(ttl=15)
def load_quizzes():
    sheet = get_gsheet()
    records = sheet.get_all_records()
    return [list(record.values()) for record in records]

@st.cache_data(ttl=15)
def load_quizzes_by_document(point_id):
    sheet = get_gsheet()
    point_id_col = sheet.col_values(2)
    matching_rows = []
    for idx, value in enumerate(point_id_col, start=1):
        if value == point_id:  # exact match
            row_data = sheet.row_values(idx)
            matching_rows.append(row_data)
    return matching_rows

def save_quiz(quiz):
    sheet = get_gsheet()
    column_values = sheet.col_values(1)
    quiz_count = len(column_values)
    if quiz_count <= 200:
        new_row = [quiz["quiz_id"], quiz["point_id"], quiz["content"], quiz["timestamp"]] 
        sheet.append_row(new_row)
        return True
    else:
        print("Exceeded 200 quizzes")
        return False


def delete_quiz(quiz_id):
    sheet = get_gsheet()
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):  # start=2 because row 1 is the header
        if row["quiz_id"] == quiz_id:
            sheet.delete_rows(idx)
            return True
    return False


BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
def to_base62(num: int) -> str:
    """Convert an integer to a Base62 string."""
    if num == 0:
        return BASE62_ALPHABET[0]
    digits = []
    base = len(BASE62_ALPHABET)
    while num:
        num, rem = divmod(num, base)
        digits.append(BASE62_ALPHABET[rem])
    return ''.join(reversed(digits))

def uuid_to_short_id(u: str, length: int = 6) -> str:
    """Convert a UUID string into a short unique Base62 ID."""
    # Convert UUID to int
    u_int = uuid.UUID(u).int
    # Encode as Base62
    short_id = to_base62(u_int)
    # Truncate or pad to desired length
    return short_id[:length]
