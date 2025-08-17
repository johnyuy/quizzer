import streamlit as st
import pandas as pd
from datetime import datetime
from service.extract_text import extract_text
from service.qdrant_utils import list_qdrant_docs, save_to_qdrant, delete_multiple_from_qdrant

MAX_DOC_SIZE = 500_000  # max characters (approx 50-70 pages of text)

# === UI ===
def doc_panel():
    st.title('Upload Document')
    st.caption('Documents will be stored in Qdrant for study/quiz generation.')

    # Initialize session state
    if "reload_docs" not in st.session_state:
        st.session_state.reload_docs = True

    # --- File Upload Section ---
    uploaded_file = st.file_uploader("Select a document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    if uploaded_file:
        if st.button("Upload"):
            file_type = uploaded_file.name.split(".")[-1].lower()
            with st.spinner("Processing file and storing in Qdrant..."):
                # Extract text safely
                try:
                    doc_text = extract_text(uploaded_file, file_type)
                except Exception as e:
                    st.error(f"Failed to extract text from this document: {e}")
                    st.stop()    
                # Check if text is empty
                if not doc_text or not doc_text.strip():
                    st.error("The document could not be processed into text. Nothing was saved.")
                else:
                    # Check document size
                    if len(doc_text) > MAX_DOC_SIZE:
                        st.warning(f"This document is too large ({len(doc_text)} chars). Please upload a smaller document.")
                        st.stop()
                    else: 
                        # Save to Qdrant
                        point_id = save_to_qdrant(doc_text, uploaded_file.name, {
                            "filename": uploaded_file.name,
                            "upload_timestamp": datetime.utcnow().isoformat()
                        })
                        st.success("Document processed and stored in Qdrant!")
                        
                        # Force reload of documents list
                        st.session_state.reload_docs = True
                        st.rerun()
    st.divider()
    st.subheader('Document List')

    # --- Fetch documents only when needed ---
    if st.session_state.reload_docs:
        with st.spinner("loading..."):
            docs = list_qdrant_docs()
            st.session_state.docs = docs
            st.session_state.reload_docs = False
    else:
        docs = st.session_state.docs

    if docs:
        docs_df = pd.DataFrame(docs)[["filename", "upload_timestamp"]].rename(
            columns={
                "filename" : "Document Name"
            }
        )
        docs_df["upload_timestamp"] = pd.to_datetime(docs_df["upload_timestamp"])
        docs_df["Uploaded On"] = docs_df["upload_timestamp"].dt.strftime("%d-%b-%Y %I:%M %p")

        st.data_editor(
            docs_df[["Document Name", "Uploaded On"]],
            column_config={
                "Document Name" : st.column_config.Column(width="large"),
                "Uploaded On" : st.column_config.Column(width="small")
            },
            hide_index=True,
            disabled=True
        )
    else:
        st.caption("No documents stored yet.")

doc_panel()   