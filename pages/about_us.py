import streamlit as st

st.title("📘 About Us")
st.markdown("---")

# Project Scope
st.header("🎯 Project Scope")
st.write("""
The **Quizzer** project is designed to provide an interactive quiz platform that helps users 
learn, practice, and test their knowledge on various topics. It aims to combine simplicity, 
engagement, and scalability to make learning more effective and enjoyable.
""")

# Objectives
st.header("📌 Objectives")
st.write("""
    - Develop an **intuitive application** that enables users to upload documents for **quiz generation** and **question answering**.  
    - Provide an **engaging user interface** that encourages learning and self-assessment.  
    - Support diverse question formats, including **multiple-choice**, **short-answer**, and **true/false**.  
    - Offer **customizable quizzes** tailored to users’ preferences and needs.  
    - Deliver **analytics and performance insights** to help users track progress.  
    - Design the system to be **extensible**, allowing seamless integration of new topics and content.  
    - Empower users to **ask questions directly from their uploaded documents** and receive intelligent, context-aware answers.  
""")

# Data Sources
st.header("📊 Data Sources")
st.write("""
The quiz questions are sourced from the documents uploaded by users.
- The uploaded documents are stored in Qdrant, a vector database, for efficient retrieval and processing.
- This vectorDB is used for :
    - generate quizzes 
    - question answering.
""")

# Features
st.header("⚡ Features")
st.write("""
- ✅ User-friendly interface powered by Streamlit.  
- ✅ Multiple question types with randomized order.  
- ✅ Scoring system with instant feedback.  
- ✅ Leaderboard support for tracking progress (future enhancement).  
- ✅ Modular structure to allow to upload new documents and generate new question banks easily.  
""")


