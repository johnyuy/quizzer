import streamlit as st
import os
import json
from datetime import datetime
import uuid
from utility import get_side_bar, check_credentials
from service.file_processor import process_file
from service.extract_text import extract_text

# LangChain & Qdrant
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.docstore.document import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointIdsList

# Configurable qdrant host via secrets

QDRANT_URL=st.secrets["QDRANT_URL"]
QDRANT_API_KEY=st.secrets["QDRANT_API_KEY"]
QDRANT_COLLECTION = "documents"
OPENAI_API_KEY=st.secrets["OPENAI_API_KEY"]

UPLOAD_FOLDER = "uploaded_docs"
METADATA_FILE = os.path.join(UPLOAD_FOLDER, "metadata.json")

# Ensure upload folder & metadata file
os.makedirs("uploaded_docs", exist_ok=True)
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "w") as f:
        json.dump([], f)

# === Qdrant setup ===
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def ensure_collection():
    """Ensure the collection exists before adding docs."""
    collections = [c.name for c in client.get_collections().collections]
    print("List of collections = ", collections)
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config={"size": 1536, "distance": "Cosine"}
        )

# VectorStore wrapper
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Qdrant(client=client, collection_name=QDRANT_COLLECTION, embeddings=embeddings)

# === File helpers ===
def save_uploaded_file(uploaded_file):
    path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def save_metadata(entry):
    with open(METADATA_FILE, "r+") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)

def delete_metadata(point_id):
    with open(METADATA_FILE, "r+") as f:
        data = json.load(f)
        data = [m for m in data if m.get("point_id") != point_id]
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)

# === Qdrant operations ===
def save_to_qdrant(doc_text, filename, metadata=None):
    ensure_collection()
    point_id = uuid.uuid4().hex
    vector = embeddings.embed_query(doc_text)
    payload = {
        "filename": filename,
        "upload_timestamp": datetime.utcnow().isoformat()
    }
    if metadata:
        payload.update(metadata)
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[{
            "id": point_id,
            "vector": vector,
            "payload": payload
        }]
    )
    return point_id

def list_qdrant_docs():
    ensure_collection()
    try:
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        docs = []
        for p in points:
            print("Point ID:", p.id)
            payload = p.payload or {}
            filename = payload.get("filename")
            upload_ts = payload.get("upload_timestamp")
            if filename:  # only include valid documents
                docs.append({
                    "point_id": p.id,
                    "filename": filename,
                    "upload_timestamp": upload_ts
                })
        return docs
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return []

def delete_multiple_from_qdrant(point_ids):
    """
    Deletes multiple documents from Qdrant using their point_ids.
    """
    try:
        if point_ids:
            # Pass the list directly, not as a dict
            client.delete(
                collection_name=QDRANT_COLLECTION,
                points_selector=PointIdsList(points=point_ids)
            )
        return True
    except Exception as e:
        st.error(f"Error deleting documents: {e}")
        return False

def get_text(file_data, file_type):
    return extract_text(file_data, file_type)

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
                doc_text = get_text(uploaded_file, file_type)
                if not doc_text or not doc_text.strip():
                    st.error("The document could not be processed into text. Nothing was saved.")
                else:
                    point_id = save_to_qdrant(doc_text, uploaded_file.name, {
                        "filename": uploaded_file.name,
                        "upload_timestamp": datetime.utcnow().isoformat()
                    })
                    save_metadata({
                        "filename": uploaded_file.name,
                        "upload_timestamp": datetime.utcnow().isoformat(),
                        "point_id": point_id
                    })
                    st.success("Document processed and stored in Qdrant!")
                    # Force reload of documents list
                    st.session_state.reload_docs = True
                    st.rerun()

    st.divider()
    st.subheader('Loaded Documents for Deletion')

    # --- Fetch documents only when needed ---
    if st.session_state.reload_docs:
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
                    # Remove from local metadata
                    for pid in selected_docs:
                        delete_metadata(pid)
                    st.success(f"Deleted {len(selected_docs)} document(s).")
                    # Reset selection and reload docs
                    st.session_state.selected_docs = []
                    st.session_state.reload_docs = True
                    st.rerun()
    else:
        st.caption("No documents stored yet.")

# === Auth ===
if not check_credentials():
    st.stop()

if st.session_state.get("role") == "admin":
    doc_panel()
    get_side_bar()
else:
    st.switch_page("pages/unauthorized.py")