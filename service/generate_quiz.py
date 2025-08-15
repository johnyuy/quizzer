from openai import OpenAI
import streamlit as st
import os
import json

OPENAI_API_KEY=st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_questions(text: str, num_questions: int = 5):
    prompt = f"""
Generate {num_questions} quiz questions based on the following text. 

Return a JSON array of questions. Each question must include:
- question: string
- type: one of ["multiple_choice", "true_false", "short_answer"]
- options: list of 3–4 strings (only for multiple_choice)
- correct_answer: string
- explanation: 2–4 sentence explanation for the correct answer
- source_excerpt: a 2–5 sentence quote or paraphrase from the text that supports the answer

Respond only with the JSON array.

Text:
{text[:4000]}
"""


    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        output = response.choices[0].message.content.strip()
        questions = json.loads(output)
        return questions
    except Exception as e:
        print(f"Error parsing questions: {e}")
        return []
