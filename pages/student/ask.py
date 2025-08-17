import time
import streamlit as st
from typing import List

from service.qdrant_utils import list_qdrant_docs, build_vectorstore, get_document_chunks
from openai import OpenAI

current_page = "ask"
if st.session_state.get("last_page") != current_page:
    st.session_state.last_page = current_page

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------- UI Header -----------------
st.title("Learn")
st.caption("Start your learning by asking a question.")

# Load list of docs from Qdrant
docs = list_qdrant_docs()
if not docs:
    st.warning("No documents found in Qdrant.")
    st.stop()

# Single selection
label_map = {f"{d['filename']} (Uploaded: {d.get('upload_timestamp','N/A')})": d for d in docs}
label = st.selectbox("Select a document", list(label_map.keys()))
selected = label_map[label]
filename = selected["filename"]

st.caption(f"Selected: **{filename}**")

# Query input
query = st.text_input("Ask a question")
k = st.slider("How many passages to retrieve", min_value=2, max_value=10, value=4)

# ----------------- Retrieval helper -----------------
def retrieve_passages_for_filename(question: str, file_name: str, k: int = 4):
    """
    Retrieve chunks for the selected filename via vector search.
    """
    vs = build_vectorstore()
    q_filter = {"must": [{"key": "filename", "match": {"value": file_name}}]}
    try:
        return vs.similarity_search(question, k=k, filter=q_filter)  
    except Exception as e:
        print(f"(Vector search failed; falling back to chunked text) Details: {e}")
        return []

# ----------------- RAG helpers -----------------
def build_prompt(question: str, contexts: List[str]) -> str:
    context_block = "\n\n".join([f"- {c}" for c in contexts])
    return (
        "You are a helpful assistant. Answer the question using ONLY the provided context. "
        "If the answer cannot be found in the context, say you don’t know.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

def answer_with_openai(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You answer questions strictly from supplied context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

# ----------------- Action -----------------
if st.button("🔎 Ask"):
    if not query.strip():
        st.warning("Please enter a question.")
        st.stop()

    start = time.time()
    with st.status("Processing Question...",expanded=True) as status:
        # Try vector-based retrieval first
        status.write("Retrieving passages...")
        retrieved = retrieve_passages_for_filename(query, filename, k=k)
        
        if retrieved:
            
            contexts = [d.page_content for d in retrieved if d and d.page_content]
            sources = [d.metadata for d in retrieved]
        else:
            # Fallback: retrieve all chunks for filename
            status.write("Retrieving from all chunks...")
            chunks = get_document_chunks(filename)
            if not chunks:
                status.update(label="No retrievable chunks found. Re-ingest document with chunked text.", state='error', expanded=True)
                st.error("No retrievable chunks found. Re-ingest document with chunked text.")
                st.stop()
            # Wrap each chunk with metadata
            contexts = []
            sources = []
            for idx, chunk_text in enumerate(chunks):
                contexts.append(chunk_text)
                sources.append({"filename": filename, "chunk_index": idx})

        # Build prompt and call OpenAI
        status.write("Calling OpenAI...")
        prompt = build_prompt(query, contexts)
        try:
            answer = answer_with_openai(prompt)
        except Exception as e:
            status.update(label="OpenAI error.", state='error', expanded=True)
            st.error(f"OpenAI error: {e}")
            st.stop()
        status.update(label="Answer Generated!", state='complete', expanded=False)
    end = time.time()

    st.subheader("Answer")
    st.write(answer)
    st.caption(f"⏱️ {end - start:.2f}s")

    # Display sources / passages
    with st.expander("Sources / Passages used"):
        for i, (ctx, meta) in enumerate(zip(contexts, sources), start=1):
            st.markdown(f"**Passage {i}** — metadata: `{meta}`")
            st.write(ctx[:1000] + ("..." if len(ctx) > 1000 else ""))
            st.markdown("---")


