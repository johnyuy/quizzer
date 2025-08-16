import streamlit as st
import pandas as pd
import gspread
import hmac
from google.oauth2.service_account import Credentials

def get_selected_document_label(doc):
    return f"{doc['filename']} (Uploaded: {doc['upload_timestamp']})"

def get_document_index(doc, docs):
    target = doc["point_id"]
    return next((i for i, p in enumerate(docs) if p['point_id'] == target), 0)


def get_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["sheets"]["quizzes"])
    return sheet.sheet1  # first worksheet


def load_quizzes():
    sheet = get_gsheet()
    records = sheet.get_all_records()
    return {row["quiz_id"]: {"point_id": row["point_id"], "content": row["content"]} for row in records}

def save_quiz(quiz):
    sheet = get_gsheet()
    column_values = sheet.col_values(1)
    quiz_count = len(column_values)
    if quiz_count <= 200:
        new_row = [quiz["quiz_id"], quiz["point_id"], quiz["content"]] 
        sheet.append_row(new_row)
        return True
    else:
        print("Exceeded 200 quizzes")
        return False