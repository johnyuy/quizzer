from langchain_openai import OpenAIEmbeddings
import numpy as np
import streamlit as st

def normalize(text: str) -> str:
    return ''.join(e.lower() for e in text if e.isalnum())

def validate_short_answer(user_answer: str, correct_answer: str) -> bool:
    embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])
    embed1 = embeddings.embed_query("user_answer")
    embed2 = embeddings.embed_query("correct_answer")

    score = np.dot(embed1, embed2)
    if score > 0.85: 
        return True
    else:
        return False

def validate_mcq_or_tf(user_answer: str, correct_answer: str) -> bool:
    return normalize(user_answer) == normalize(correct_answer)
