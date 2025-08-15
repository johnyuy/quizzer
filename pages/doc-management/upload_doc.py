import streamlit as st
from datetime import datetime
from service.extract_text import extract_text
from service.qdrant_utils import list_qdrant_docs, save_to_qdrant, delete_multiple_from_qdrant

print(st.session_state)
MAX_DOC_SIZE = 500_000  # max characters (approx 50-70 pages of text)

# === UI ===
def doc_panel():
    st.title('Upload Document')
    st.caption('Documents will be stored in Qdrant for study/quiz generation.')

    # Initialize session state
    if "reload_docs" not in st.session_state:
        st.session_state.reload_docs = True
    if "selected_docs" not in st.session_state:
        st.session_state.selected_docs = []

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
        selected_docs = st.session_state.selected_docs.copy()  # local copy to manage checkboxes

        # --- Render checkboxes ---
        for doc in docs:
            key = f"select_{doc['point_id']}"
            checked = st.checkbox(
                f"{doc['filename']} (Uploaded: {doc.get('upload_timestamp','N/A')})",
                key=key,
                value=doc['point_id'] in selected_docs
            )
            if checked and doc['point_id'] not in selected_docs:
                selected_docs.append(doc['point_id'])
            elif not checked and doc['point_id'] in selected_docs:
                selected_docs.remove(doc['point_id'])

        st.session_state.selected_docs = selected_docs

        # --- Delete selected documents ---
        if selected_docs and st.button("Delete Selected"):
            with st.spinner(f"Deleting {len(selected_docs)} document(s)..."):
                success = delete_multiple_from_qdrant(selected_docs)
                if success:
                    st.success(f"Deleted {len(selected_docs)} document(s).")
                    # Reset selection and reload docs
                    st.session_state.selected_docs = []
                    st.session_state.reload_docs = True
                    st.rerun()
    else:
        st.caption("No documents stored yet.")

doc_panel()   