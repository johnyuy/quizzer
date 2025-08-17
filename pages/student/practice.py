import streamlit as st
import time
import io
from datetime import datetime

from service.generate_quiz import generate_questions
from service.validation import validate_mcq_or_tf, validate_short_answer
from service.qdrant_utils import list_qdrant_docs, get_document_text

# --- Session State Initialization ---
for key, default in {
    "questions": None,
    "q_index": None,
    "user_answers": {},
    "score": 0,
    "verified": False,
    "correct": False,
    "text": None,
    "selected_doc": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def clear():
    st.session_state["questions"] = None
    st.session_state["q_index"] = None
    st.session_state["v_index"] = None
    st.session_state["user_answers"] = {}
    st.session_state["score"] = 0
    st.session_state["verified"] = False
    st.session_state["correct"] = False
    st.session_state["text"] = None

st.title("Practice")
st.caption("Generate questions and test your knowledge.")

current_page = "practice"
if st.session_state.get("last_page") != current_page:
    clear()
    st.session_state.last_page = current_page

# --- Load available documents ---
docs = list_qdrant_docs()
if not docs:
    st.warning("No documents available in Qdrant.")
    st.stop()

# Number of questions
num_questions = st.number_input("Number of questions", min_value=1, max_value=10, value=3)

# --- Document selection ---
doc_map = {f"{doc['filename']} (Uploaded: {doc['upload_timestamp']})": doc for doc in docs}
selected_label = st.selectbox("Select a document", list(doc_map.keys()))

selected_doc = doc_map[selected_label]
st.session_state.selected_doc = selected_doc

# --- Generate Quiz ---
if st.button("Generate Questions",  use_container_width=True):
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
            st.session_state.questions = questions
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.user_answers = {}
            st.session_state.verified = False
            st.rerun()
        else:
            st.error("Failed to generate questions.")

# --- Display Questions ---
if st.session_state.questions:
    q_idx = st.session_state.q_index
    question = st.session_state.questions[q_idx]
    st.markdown(f"### Question {q_idx + 1}: {question['question']}")

    input_key = f"user_answer_{q_idx}"
    user_answer = None

    if question["type"] == "multiple_choice":
        user_answer = st.radio("Choose one:", question["options"], key=input_key)
    elif question["type"] == "true_false":
        user_answer = st.radio("Select True or False:", ["True", "False"], key=input_key)
    elif question["type"] == "short_answer":
        user_answer = st.text_input("Your answer:", key=input_key)

    if st.button("Verify Answer", use_container_width=True, ):
        if user_answer:
            correct_answer = question["correct_answer"]

            if question["type"] in ["multiple_choice", "true_false"]:
                is_correct = validate_mcq_or_tf(user_answer, correct_answer)
            else:
                is_correct = validate_short_answer(user_answer, correct_answer)

            st.session_state.verified = True
            st.session_state.correct = is_correct

            st.session_state.user_answers[q_idx] = {
                "question": question["question"],
                "your_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct
            }

            if is_correct:
                st.session_state.score += 1
            st.rerun()
        else:
            st.warning("Please enter or select an answer first.")

    if st.session_state.verified:
        if st.session_state.correct:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Incorrect. Correct answer: **{question['correct_answer']}**")

        explanation = question.get("explanation", "")
        if explanation:
            st.info(f"ℹ️ **Explanation:** {explanation}")

        source_excerpt = question.get("source_excerpt", "")
        if source_excerpt:
            st.code(f"📄 Source: {source_excerpt}", language="markdown")

        if q_idx + 1 < len(st.session_state.questions):
            if st.button("Next Question",  use_container_width=True):
                st.session_state.q_index += 1
                st.session_state.verified = False
                st.rerun()
        else:
            st.success(f"🎉 Practice Completed! Final Score: {st.session_state.score} / {len(st.session_state.questions)}")

# --- Download ---
def prepare_download_content(questions):
    output = io.StringIO()
    for i, q in enumerate(questions):
        output.write(f"Q{i + 1}: {q['question']}\n")
        output.write(f"Type: {q['type']}\n")
        output.write(f"Correct Answer: {q['correct_answer']}\n")

        if q.get("explanation"):
            output.write(f"Explanation: {q['explanation']}\n")
        if q.get("source_excerpt"):
            output.write(f"Source: {q['source_excerpt']}\n")

        output.write("\n" + "-" * 40 + "\n\n")
    return output.getvalue()

if st.session_state.questions:
    download_text = prepare_download_content(st.session_state.questions)
    st.download_button(
        label="⬇️ Download Questions & Answers",
        data=download_text,
        file_name="quiz_answers.txt",
        mime="text/plain",
        use_container_width=True
    )
