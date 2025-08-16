import streamlit as st
import uuid
from datetime import datetime, timezone, timedelta


# LangChain & Qdrant
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Qdrant as LCQdrant
from langchain.text_splitter import CharacterTextSplitter

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointIdsList, VectorParams, PayloadSchemaType

# Configurable qdrant host via secrets
QDRANT_URL = st.secrets["QDRANT_URL"]
QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

QDRANT_COLLECTION = "documents"

# === Qdrant setup ===
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = LCQdrant(client=client, collection_name=QDRANT_COLLECTION, embeddings=embeddings)

def ensure_collection():
    """Ensure the collection exists and 'filename' payload is indexed for filtering."""
    collections = [c.name for c in client.get_collections().collections]
    
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print(f"Created collection '{QDRANT_COLLECTION}'")

    # Try to create payload index for 'filename'; ignore error if it already exists
    try:
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="filename",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("Payload index on 'filename' created successfully")
    except Exception as e:
        if "already exists" in str(e):
            print("Payload index on 'filename' already exists")
        else:
            print(f"Failed to create payload index: {e}")

def list_qdrant_docs():
    ensure_collection()
    try:
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=500,
            with_payload=True,
            with_vectors=False
        )
        docs = []
        for p in points:
            payload = p.payload or {}
            filename = payload.get("filename")
            upload_ts = payload.get("upload_timestamp")
            if filename and payload.get("chunk_index") == 0:  # only list once per doc
                docs.append({
                    "point_id": p.id,
                    "filename": filename,
                    "upload_timestamp": upload_ts
                })
        return docs
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return []

def save_to_qdrant(doc_text, filename, metadata=None, chunk_size=2000, chunk_overlap=0, batch_size=50):
    ensure_collection()
    
    # Split document into chunks
    splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(doc_text)

    point_ids = []
    points = []

    for idx, chunk in enumerate(chunks):
        point_id = uuid.uuid4().hex
        vector = embeddings.embed_query(chunk)
        payload = {
            "filename": filename,
            "upload_timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "chunk_index": idx,
            "chunk_text": chunk
        }
        if idx == 0:
            payload["document_text"] = doc_text  # keep full text for quiz generation
        if metadata:
            payload.update(metadata)

        points.append({
            "id": point_id,
            "vector": vector,
            "payload": payload
        })
        point_ids.append(point_id)

        # Upsert in batches
        if len(points) >= batch_size:
            client.upsert(collection_name=QDRANT_COLLECTION, points=points)
            points = []

    # Upsert remaining points
    if points:
        client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    
    return point_ids


def delete_multiple_from_qdrant(point_ids):
    """Deletes multiple documents from Qdrant using their point_ids."""
    try:
        if point_ids:
            client.delete(
                collection_name=QDRANT_COLLECTION,
                points_selector=PointIdsList(points=point_ids)
            )
        return True
    except Exception as e:
        st.error(f"Error deleting documents: {e}")
        return False

def get_document_text(point_id=None, filename=None):
    """
    Retrieve document text from Qdrant.
    Can fetch by point_id (first chunk) or by filename (all chunks concatenated).
    """
    try:
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        chunks = []

        for p in points:
            payload = p.payload or {}

            # If fetching by point_id
            if point_id and p.id == point_id:
                doc_text = payload.get("document_text") or payload.get("chunk_text")
                return doc_text if doc_text else ""

            # If fetching by filename
            if filename and payload.get("filename") == filename:
                chunk_text = payload.get("chunk_text") or payload.get("document_text")
                if chunk_text:
                    chunks.append(chunk_text)

        # Concatenate all chunks if fetching by filename
        if filename and chunks:
            return "\n".join(chunks)

        return ""
    except Exception as e:
        st.error(f"Error fetching document text: {e}")
        return ""


def build_vectorstore() -> LCQdrant:
    """Create a LangChain Qdrant vectorstore for retrieval."""
    return LCQdrant(client=client, collection_name=QDRANT_COLLECTION, embeddings=embeddings)


def get_document_chunks(filename):
    points, _ = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=1000,
        with_payload=True,
        with_vectors=False
    )
    chunks = []
    for p in points:
        payload = p.payload or {}
        if payload.get("filename") == filename and payload.get("chunk_text") is not None:
            chunks.append((payload.get("chunk_index", 0), payload["chunk_text"]))
    # Sort by chunk_index
    chunks.sort(key=lambda x: x[0])
    return [c[1] for c in chunks]  # return only text