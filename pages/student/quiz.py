import streamlit as st
import ast
import time
from datetime import datetime, timezone, timedelta
from service.track_quiz import load_quizzes, load_quizzes_by_document, get_document_index
from service.qdrant_utils import list_qdrant_docs
from service.validation import validate_mcq_or_tf, validate_short_answer
from service.track_results import save_result, string_to_uuid
from gspread.exceptions import APIError


def reset():
    for key, default in {
        "questions_q": None,
        "q_index_q": None,
        "v_index_q": None,
        "user_answers_q": {},
        "score_q": 0,
        "verified_q": False,
        "correct_q": False,
        "text_q": None,
        "selected_doc": None,
        "start" : ""
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

def clear():
    st.session_state["questions_q"] = None
    st.session_state["q_index_q"] = None
    st.session_state["v_index_q"] = None
    st.session_state["user_answers_q"] = {}
    st.session_state["score_q"] = 0
    st.session_state["verified_q"] = False
    st.session_state["correct_q"] = False
    st.session_state["text_q"] = None
    st.session_state["start"] = ""

current_page = "quiz"
if st.session_state.get("last_page") != current_page:
    clear()
    st.session_state.last_page = current_page

@st.dialog("🎉 Quiz Completed!")
def show_result(score: int, total : int):
    st.write(f"Final Score: {score} / {total}")
    if st.button("Done"):
        clear()
        st.switch_page("pages/student/result.py")

try:
    st.title("Quiz")
    st.caption("Your results will be recorded.")

    # Initialize session state
    if "reload_docs" not in st.session_state:
        st.session_state.reload_docs = True
    if "quizzes" not in st.session_state:
        st.session_state["quizzes"] = []

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

    selected_label = st.selectbox("Select a Document", options, on_change=clear)

    quizzes = st.session_state["quizzes"]
    if not quizzes or (doc_map[selected_label]["point_id"] != selected_document["point_id"]):
        
        filter_doc = doc_map[selected_label]
        st.session_state["selected_doc"] = filter_doc
        raw_quizzes = load_quizzes_by_document(filter_doc["point_id"])
        
        if not raw_quizzes:
            st.info("There are no quizzes generated from this document.")
            st.stop()
        
        for data in raw_quizzes:
            questions = ast.literal_eval(data[2])
            quiz = {
                "quiz_id" : data[0],
                "point_id" : data[1],
                "timestamp" : data[3],
                "content" : questions
                }
            quizzes.append(quiz) 
        st.session_state["quizzes"] = quizzes

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
                st.session_state["questions_q"] = quiz["content"]
                st.session_state["q_index_q"] = 0
                st.session_state["v_index_q"] = 0
                st.session_state["score_q"] = 0
                st.session_state["user_answers_q"] = {}
                st.session_state["verified_q"] = False
                st.session_state["start"] = datetime.now(timezone(timedelta(hours=8))).isoformat()
                st.rerun()


        if "questions_q" in st.session_state and st.session_state["questions_q"] is not None:
            
            q_idx = st.session_state["q_index_q"]
            question = st.session_state.questions_q[q_idx]
            filename =  docs[get_document_index(quiz, docs)]['filename']
            title = f"Quiz#{quiz['quiz_id']} - {filename}"
            st.write("")
            st.caption(title)

            completed = False


            with st.expander(f"### Question {q_idx + 1}/{len(st.session_state["questions_q"])}: {question['question']}", expanded=True):

                input_key = f"user_answer_{q_idx}"
                user_answer = None
                if question["type"] == "multiple_choice":
                    user_answer = st.radio("Choose one:", question["options"], key=input_key, disabled=st.session_state["v_index_q"]>st.session_state["q_index_q"])
                elif question["type"] == "true_false":
                    user_answer = st.radio("Select True or False:", ["True", "False"], key=input_key, disabled=st.session_state["v_index_q"]>st.session_state["q_index_q"])
                elif question["type"] == "short_answer":
                    user_answer = st.text_input("Your answer:", key=input_key, disabled=st.session_state["v_index_q"]>st.session_state["q_index_q"])

                # with st.spinner(""):
                if st.button("Verify Answer", use_container_width=True, disabled=st.session_state["v_index_q"]>st.session_state["q_index_q"]):
                    st.session_state["v_index_q"]+=1

                    if user_answer:
                        correct_answer = question["correct_answer"]
                        if question["type"] in ["multiple_choice", "true_false"]:
                            is_correct = validate_mcq_or_tf(user_answer, correct_answer)
                        else:
                            is_correct = validate_short_answer(user_answer, correct_answer)


                        st.session_state.verified_q = True
                        st.session_state.correct_q = is_correct

                        st.session_state.user_answers_q[q_idx] = {
                            "question": question["question"],
                            "your_answer": user_answer,
                            "correct_answer": correct_answer,
                            "is_correct": is_correct
                        }

                        if is_correct:
                            st.session_state.score_q += 1
                        
                    else:
                        st.warning("Please enter or select an answer first.")
                    st.rerun()

                if st.session_state.verified_q:
                    if st.session_state.correct_q:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Incorrect. Correct answer: **{question['correct_answer']}**")

                    explanation = question.get("explanation", "")
                    if explanation:
                        st.info(f"ℹ️ **Explanation:** {explanation}")

                    source_excerpt = question.get("source_excerpt", "")
                    if source_excerpt:
                        st.code(f"📄 Source: {source_excerpt}", language="markdown")

                    if q_idx + 1 < len(st.session_state.questions_q):
                        if st.button("Next Question", use_container_width=True):
                            st.session_state.q_index_q += 1
                            st.session_state.verified_q = False
                            # wait 1 seconds
                            progress = st.progress(0)
                            for i in range(11): 
                                progress.progress(i/11)
                                time.sleep(0.1)
                            progress.empty()
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
                    "score" : st.session_state.score_q,
                    "answers" : str(st.session_state.user_answers_q),
                    "timestamp": st.session_state["start"]
                }):
                    print(f"User {st.session_state["username_logged"]} completed quiz id {quiz['quiz_id']}")
                else:
                    print("Unable to save result, duplicate id")
                show_result(st.session_state.score_q, len(st.session_state.questions_q))
except APIError as e:
    print("APIError occurred:", e)
    
    # wait 10 seconds
    with st.spinner("Request quota limit exceeded, please wait..."):
        progress = st.progress(0)
        for i in range(201): 
            percent = int(i / 200 * 100)  # scale 0–200 → 0–100
            progress.progress(percent)
            time.sleep(0.1)
        progress.empty()
    st.rerun()
