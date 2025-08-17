from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
import numpy as np
import streamlit as st

def normalize(text: str) -> str:
    return ''.join(e.lower() for e in text if e.isalnum())

def validate_short_answer(user_answer: str, correct_answer: str) -> bool:
    OPENAI_API_KEY=st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
You are a strict answer validator.
The correct answer is: "{correct_answer}"
The user answered: "{user_answer}"

Rules:
- If the meaning of the user answer is essentially the same as the correct answer, respond ONLY with "YES".
- Otherwise, respond ONLY with "NO".
- Do not explain.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # fast + cheap, good for judgments
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # deterministic
    )

    answer = response.choices[0].message.content.strip().upper()
    return answer == "YES"

def validate_mcq_or_tf(user_answer: str, correct_answer: str) -> bool:
    return normalize(user_answer) == normalize(correct_answer)
