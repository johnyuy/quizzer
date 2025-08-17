import streamlit as st
import ast
import pandas as pd
from datetime import datetime
from service.track_quiz import load_quizzes, load_quizzes_by_document, get_document_index, delete_quiz
from service.track_results import load_results_by_quiz_id, int_keys_to_str
from service.qdrant_utils import list_qdrant_docs

@st.dialog("Results", width="large")
def view_result(result):
    if not result:
        st.write("No results found.")
    else:
        result_df = pd.DataFrame(result[1:], columns=result[0])
        result_df = result_df.drop(columns=["quiz_id", "result_id","point_id"]).rename(
            columns={
                "username" : "Username",
                "filename" : "Document Name",
                "score" : "Score",
                "answers" : "Answers",
                "timestamp" : "Taken On",
        })
        result_df["Taken On"] = pd.to_datetime(result_df["Taken On"])
        final_df = result_df.copy()
        final_df.sort_values(by="Taken On", ascending=False)
        final_df["Answers"] = final_df["Answers"].apply(ast.literal_eval)
        final_df["Answers"] = final_df["Answers"].apply(int_keys_to_str)
        st.dataframe(
            final_df,
            column_config={
                "Answers" : st.column_config.JsonColumn(
                    "Answers (double click to expand)", 
                    help="click to expand",
                    width=210),
                "Score": st.column_config.NumberColumn(width=50)
            },
            hide_index=True)

st.title("View Quizzes")
st.write("")
# Initialize session state
if "reload_docs" not in st.session_state:
    st.session_state.reload_docs = True
if "selected_docs" not in st.session_state:
    st.session_state.selected_docs = []

# --- Fetch documents only when needed ---
if st.session_state.reload_docs:
    with st.spinner("loading..."):
        docs = list_qdrant_docs()
        st.session_state.docs = docs
        st.session_state.reload_docs = False
else:
    docs = st.session_state.docs

if not docs:
    st.caption("No documents stored yet.")
    st.stop()


doc = None
if "selected_doc" in st.session_state:
    doc = st.session_state["selected_doc"]

doc_map = {f"{doc['filename']} (Uploaded: {doc['upload_timestamp']})": doc for doc in docs}
options = list(doc_map.keys())
options.insert(0, "All")

index = 0

if doc:
    index = get_document_index(doc, docs) + 1



selected_label = st.selectbox("Filter by document", options, index=index)
st.write("")
with st.spinner("loading"):
    if selected_label == "All":
        raw_quizzes = load_quizzes()
    else:
        filter_doc = doc_map[selected_label]
        raw_quizzes = load_quizzes_by_document(filter_doc["point_id"])

    if not raw_quizzes:
        st.info("There are no quizzes generated from this document.")
    
    else:
        quizzes = []
        for data in raw_quizzes:
            questions = ast.literal_eval(data[2])
            quiz = {
                "quiz_id" : data[0],
                "point_id" : data[1],
                "timestamp" : data[3],
                "content" : questions
                }
            quizzes.append(quiz) 
        max = len(quizzes)
        for i, quiz in enumerate(quizzes):
            dt = datetime.fromisoformat(quiz['timestamp'])
            with st.container(horizontal=True):
                with st.expander(label=f"Quiz#{quiz['quiz_id']}  -  Generated {dt.strftime("%d-%b-%Y %I:%M %p")}", expanded=i==max-1, width=500):
                    for j, question in enumerate(quiz["content"]):
                        with st.expander(label=f"Question#{j+1}: {question["question"]}", expanded=False, icon=":material/help:", width=500):
                            type = question["type"]
                            if type == "multiple_choice":
                                with st.expander("Options", expanded=False):
                                    for k, option in enumerate(question["options"]):
                                        st.write(f"{k+1}) {option}")
                            with st.expander("Answer", expanded=False, icon=":material/check_circle:"):
                                st.write(question["correct_answer"])
                if st.button("Results", key=f"quiz-result-{i}", use_container_width=True):
                    print(f"View results for quiz id={quiz['quiz_id']}")
                    results = load_results_by_quiz_id(quiz['quiz_id'])
                    view_result(results)
                if st.button("",icon=':material/delete:', key=f"quiz-delete-{i}", use_container_width=True, type='primary'):
                    print(f"Delete quiz id={quiz['quiz_id']}")
                    if delete_quiz(quiz['quiz_id']):
                        st.toast("Quiz deleted")
                        st.rerun()
                    else:
                        st.error("Unable to delete quiz")
            st.write("")