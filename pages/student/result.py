import streamlit as st
import pandas as pd
import ast
from service.track_results import load_results_by_username, int_keys_to_str


username = st.session_state["username_logged"]

st.title(f"{str(username).title()}'s Results")


results = load_results_by_username(username)

if not results:
    st.info("No results found.")
    st.stop()

result_df = pd.DataFrame(results[1:], columns=results[0])
result_df = result_df.drop(columns=["result_id","point_id","username"]).rename(
    columns={
        "quiz_id" : "Quiz#",
        "filename" : "Document Name",
        "score" : "Score",
        "answers" : "Answers",
        "timestamp" : "Taken On",
})
result_df["Taken On"] = pd.to_datetime(result_df["Taken On"])
new_order = ["Taken On", "Document Name", "Quiz#", "Score", "Answers"]
result_df = result_df[new_order]

# filter by filename
documents = ["All"] + result_df["Document Name"].unique().tolist()
selected_document = st.selectbox("Filter by Document", documents)

with st.spinner("Loading"):
    filtered_df = result_df.copy()
    filtered_df = filtered_df.sort_values(by="Taken On", ascending=False)
    filtered_df["Answers"] = filtered_df["Answers"].apply(ast.literal_eval)
    filtered_df["Answers"] = filtered_df["Answers"].apply(int_keys_to_str)

    if selected_document != "All":
        filtered_df = filtered_df[filtered_df["Document Name"] == selected_document]
        filtered_df = filtered_df.drop(columns=["Document Name"])

    st.dataframe(
        filtered_df, 
        column_config={
            "Answers" : st.column_config.JsonColumn(
                "Answers (double click to expand)", 
                help="click to expand",
                width=210),
            "Score": st.column_config.NumberColumn(width=50),
            "Quiz#": st.column_config.TextColumn(width=60)
        },
        hide_index=True)