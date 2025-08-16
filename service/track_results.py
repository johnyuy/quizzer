import streamlit as st
import uuid
import gspread
from google.oauth2.service_account import Credentials


def get_results_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["sheets"]["quizzes"])
    return sheet.get_worksheet(1)  # second worksheet

def load_all_results():
    sheet = get_results_gsheet()
    records = sheet.get_all_records()
    return [list(record.values()) for record in records]

def load_results_by_document(point_id):
    sheet = get_results_gsheet()
    point_id_col = sheet.col_values(2)
    matching_rows = []
    for idx, value in enumerate(point_id_col, start=1):
        if value == point_id:  # exact match
            row_data = sheet.row_values(idx)
            matching_rows.append(row_data)
    return matching_rows

def load_results_by_quiz_id(quiz_id):
    sheet = get_results_gsheet()
    quiz_id_col = sheet.col_values(1)
    matching_rows = []
    for idx, value in enumerate(quiz_id_col, start=1):
        if value == quiz_id:  # exact match
            row_data = sheet.row_values(idx)
            matching_rows.append(row_data)
    return matching_rows

def save_result(result):
    sheet = get_results_gsheet()
    # TODO
    # if username in users:
    #     st.error("User already exists!")
    new_row = [
        result["result_id"],
        result["quiz_id"],
        result["point_id"],
        result["filename"],
        result["username"],
        result["score"],
        result["answers"],
        result["timestamp"]] 
    sheet.append_row(new_row)

def string_to_uuid(s: str) -> uuid.UUID:
    # UUID5 uses SHA-1, deterministic for (namespace, name) pair
    return uuid.uuid5(uuid.NAMESPACE_DNS, s)