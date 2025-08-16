import streamlit as st
import time
from datetime import datetime, timezone, timedelta
import uuid
from urllib.parse import quote, unquote

from service.generate_quiz import generate_questions
from service.qdrant_utils import list_qdrant_docs, get_document_text
from service.track_quiz import save_quiz, uuid_to_short_id

st.set_page_config(page_title="Generate Quiz", layout="centered")
st.title("Generate Quiz")



# --- Load available documents ---
docs = list_qdrant_docs()
if not docs:
    st.warning("No documents available in Qdrant.")
    st.stop()

index = 0
if "selected_document_index_for_quiz_generation" in st.session_state:
    index = st.session_state["selected_document_index_for_quiz_generation"]

# Number of questions
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

# --- Document selection ---
doc_map = {f"{doc['filename']} (Uploaded: {doc['upload_timestamp']})": doc for doc in docs}
selected_label = st.selectbox(
    "Select a document",
    list(doc_map.keys()),
    index=index)

selected_doc = doc_map[selected_label]
st.session_state.selected_doc = selected_doc

# --- Generate Quiz ---
if st.button("Generate", use_container_width=True):
    point_id = selected_doc["point_id"]
    with st.spinner("Loading document text from Qdrant..."):
        doc_text = get_document_text(point_id)

    if not doc_text:
        st.error("This document has no stored text in Qdrant.")
        st.stop()

    st.session_state.text = doc_text

    with st.spinner("Generating Quiz using AI..."):
        start = time.time()
        try:
            questions = generate_questions(doc_text, num_questions)
        except Exception as e:
            st.error(f"Quiz generation failed: {e}")
            st.stop()
        end = time.time()
        st.text(f"⏱️ AI took {end - start:.2f} seconds")

        if questions:
            length = len(str(questions))
            if(length > 50000):
                st.error("Questions generated are too long")
            else:
                quiz_id = uuid_to_short_id(str(uuid.uuid4()))
                print(f"storing new quiz_id={quiz_id}, length={length}")
                if save_quiz({
                    "quiz_id": quiz_id,
                    "point_id": point_id,
                    "content": str(questions),
                    "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat()
                    }):
                    st.toast("Quiz Generated", icon = ":material/check_circle:")
                    st.session_state["generated_quiz_id"] = quiz_id
                    time.sleep(1.5)
                    st.switch_page("pages/quiz-management/manage_quiz.py")
                else:
                    st.error("Failed to store questions.")
        else:
            st.error("Failed to generate questions.")

