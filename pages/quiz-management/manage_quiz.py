import streamlit as st
import ast
from datetime import datetime
from service.track_quiz import load_quizzes, load_quizzes_by_document, get_document_index, delete_quiz
from service.qdrant_utils import list_qdrant_docs


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
                if st.button("Results", icon=":material/file_download:", key=f"quiz-result-{i}", use_container_width=True):
                    print(f"View results for quiz id={quiz['quiz_id']}")
                if st.button("",icon=':material/delete:', key=f"quiz-delete-{i}", use_container_width=True, type='primary'):
                    print(f"Delete quiz id={quiz['quiz_id']}")
                    if delete_quiz(quiz['quiz_id']):
                        st.toast("Quiz deleted")
                        st.rerun()
                    else:
                        st.error("Unable to delete quiz")
            st.write("")