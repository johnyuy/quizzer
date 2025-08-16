import streamlit as st
from datetime import datetime
import time
from service.qdrant_utils import list_qdrant_docs, delete_multiple_from_qdrant
from service.track_quiz import get_document_index


@st.dialog("Confirm Delete")
def confirm_delete(document):
    st.write(f"Delete {document["filename"]} (uploaded on {document["upload_timestamp"]})? ")
    if st.button("Confirm"):
        print(f"Confirm delete {document["filename"]}")
        success = False
        with st.spinner(f"Deleting {document["filename"]}..."):
            success = delete_multiple_from_qdrant([document["point_id"]])
            time.sleep(1.5)
        if success:
            st.success(f"Deleted {document["filename"]}.")
            st.session_state.reload_docs = True
            time.sleep(1.5)
            st.rerun()


MAX_DOC_SIZE = 500_000  # max characters (approx 50-70 pages of text)

st.title('Documents')

# Initialize session state
if "reload_docs" not in st.session_state:
    st.session_state.reload_docs = True
if "selected_docs" not in st.session_state:
    st.session_state.selected_docs = []

st.write('')

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

st.markdown("""
    <style>
    .title {
        font-weight: bold;
        font-size: 14px;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)     

# st.markdown('<div class="grid-container">', unsafe_allow_html=True)
with st.container(horizontal=True, width='stretch', horizontal_alignment='left'):
    for document in docs:
        with st.container(width=320, horizontal_alignment='center', border=True):
            with st.container(horizontal=True, vertical_alignment='top'):
                with st.container(width=220, height=100, border=False, vertical_alignment='top'):
                    st.markdown(f"""<div class="title">{document['filename']}</div>""", unsafe_allow_html=True)
                    dt = datetime.fromisoformat(document['upload_timestamp'])
                    st.caption(f"Uploaded {dt.strftime("%d-%b-%Y %I:%M %p")}")
                with st.container(width=35, border=False, vertical_alignment='top'):
                    if st.button("", icon=':material/delete:', key=f"delete-{document['point_id']}", use_container_width=True):
                        print(f"To delete {document['filename']}")
                        confirm_delete(document)
                with st.container(horizontal=True, horizontal_alignment='left'): 
                    if st.button("Generate Quiz", icon=":material/psychology:", key=f"generate-quiz-{document['point_id']}", width=155, type='primary'):
                        print(f"Generating quiz for {document['point_id']}")
                        index=get_document_index(document, docs)
                        st.session_state["selected_document_index_for_quiz_generation"]=index
                        st.switch_page("pages/quiz-management/generate_quiz.py")
                    if st.button("Results", icon=":material/file_download:", key=f"quiz-result-{document['point_id']}", width=105):
                        print(f"Downloading results for {document['point_id']}")
            
                            
                    
