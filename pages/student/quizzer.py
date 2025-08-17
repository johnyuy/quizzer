import streamlit as st
import ast
from datetime import datetime, timezone, timedelta
from service.track_quiz import load_quizzes, load_quizzes_by_document, get_document_index
from service.qdrant_utils import list_qdrant_docs
from service.validation import validate_mcq_or_tf, validate_short_answer
from service.track_results import save_result, string_to_uuid
from gspread.exceptions import APIError


def reset():
    for key, default in {
        "questions": None,
        "q_index": None,
        "user_answers": {},
        "score": 0,
        "verified": False,
        "correct": False,
        "text": None,
        "selected_doc": None,
        "start" : ""
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

def clear():
    st.session_state["questions"] = None
    st.session_state["q_index"] = None
    st.session_state["user_answers"] = {}
    st.session_state["score"] = 0
    st.session_state["verified"] = False
    st.session_state["correct"] = False
    st.session_state["text"] = None
    st.session_state["start"] = ""

@st.dialog("🎉 Quiz Completed!")
def show_result(score: int, total : int, rerun : bool = True):
    st.write(f"Final Score: {score} / {total}")
    if st.button("Done"):
        clear()
        st.switch_page("pages/student/result.py")
        # if rerun:
        #     st.rerun()
        # else:
        #     st.switch_page("pages/student/quizzer.py")

try:
    st.title("Test Your Knowledge")
    st.write("")

    # Initialize session state
    if "reload_docs" not in st.session_state:
        st.session_state.reload_docs = True

    # --- Fetch documents only when needed ---
    if st.session_state.reload_docs:
        with st.spinner("loading..."):
            docs = list_qdrant_docs()
            st.session_state.docs = docs
            st.session_state["reload_docs"] = False
    else:
        docs = st.session_state.docs

    if not docs:
        st.caption("No documents stored yet.")
        st.stop()


    selected_document = None
    if "selected_doc" in st.session_state:
        selected_document = st.session_state["selected_doc"]

    doc_map = {f"{doc['filename']} (Uploaded: {doc['upload_timestamp']})": doc for doc in docs}
    options = list(doc_map.keys())
    options.insert(0, "All")

    index = 0

    if selected_document:
        index = get_document_index(selected_document, docs) + 1


    selected_label = st.selectbox("Select a Document", options, index=index, on_change=clear)
    st.write("")

    if selected_label == "All":
        raw_quizzes = load_quizzes()
    else:
        filter_doc = doc_map[selected_label]
        raw_quizzes = load_quizzes_by_document(filter_doc["point_id"])

    if not raw_quizzes:
        st.info("There are no quizzes generated from this document.")
        st.stop()

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

    quiz_map = {f"Quiz#{quiz['quiz_id']}  -  Generated {datetime.fromisoformat(quiz['timestamp']).strftime("%d-%b-%Y %I:%M %p")}": quiz for i, quiz in enumerate(quizzes)}
    quiz_options = list(quiz_map.keys())
    quiz = None
    with st.container():
        with st.container(horizontal=True, vertical_alignment='bottom'):
            selected_quiz = st.selectbox("Select a Quiz", quiz_options, index=len(quiz_options)-1, width=500, on_change=clear)
            quiz = quiz_map[selected_quiz]
            
            if st.button("Start", use_container_width=True, type='primary'):
                print(f"User {st.session_state['username_logged']} started quiz id {quiz['quiz_id']}")
                reset()
                st.session_state["questions"] = quiz["content"]
                st.session_state["q_index"] = 0
                st.session_state["score"] = 0
                st.session_state["user_answers"] = {}
                st.session_state["verified"] = False
                st.session_state["start"] = datetime.now(timezone(timedelta(hours=8))).isoformat()
                st.rerun()


        if "questions" in st.session_state and st.session_state["questions"] is not None:
            
            q_idx = st.session_state.q_index
            question = st.session_state.questions[q_idx]
            filename =  docs[get_document_index(quiz, docs)]['filename']
            title = f"Quiz#{quiz['quiz_id']} - {filename}"
            st.write("")
            st.caption(title)

            completed = False
            with st.expander(f"### Question {q_idx + 1}/{len(st.session_state["questions"])}: {question['question']}", expanded=True):

                input_key = f"user_answer_{q_idx}"
                user_answer = None
                if question["type"] == "multiple_choice":
                    user_answer = st.radio("Choose one:", question["options"], key=input_key)
                elif question["type"] == "true_false":
                    user_answer = st.radio("Select True or False:", ["True", "False"], key=input_key)
                elif question["type"] == "short_answer":
                    user_answer = st.text_input("Your answer:", key=input_key)

                with st.spinner(""):
                    if st.button("Verify Answer"):
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
                            # st.rerun()
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
                            if st.button("Next Question"):
                                st.session_state.q_index += 1
                                st.session_state.verified = False
                                st.rerun()
                        else:
                            completed = True
            if(completed):
                if save_result({
                    "result_id" : string_to_uuid(
                        f"{quiz['point_id']}-{quiz['quiz_id']}-{st.session_state["username_logged"]}-{st.session_state["start"]}"),
                    "quiz_id" : quiz['quiz_id'],
                    "point_id" : quiz['point_id'],
                    "filename" : filename,
                    "username" : st.session_state["username_logged"],
                    "score" : st.session_state.score,
                    "answers" : str(st.session_state.user_answers),
                    "timestamp": st.session_state["start"]
                }):
                    print(f"User {st.session_state["username_logged"]} completed quiz id {quiz['quiz_id']}")
                    show_result(st.session_state.score, len(st.session_state.questions))
                else:
                    print("Unable to save result, duplicate id")
                    show_result(st.session_state.score, len(st.session_state.questions), False)
except APIError as e:
    print("APIError occurred:", e)
    st.error("Error encountered. Please try again.")