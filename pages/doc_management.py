import streamlit as st
import os
from utility import get_side_bar, check_credentials
from service.file_processor import process_file

def doc_panel():
    with st.container(gap='small'):
        st.title('Upload Document')

    to_generate = False
    st.caption('This document will be used to generate quizzes.')

    uploaded_file = st.file_uploader("Choose a file") # TODO add filter for file extension types
    if uploaded_file is not None:
        file_path = os.path.abspath(uploaded_file.name)
        print(f'selected: {file_path}')
        with st.container(horizontal_alignment='center'):
            if st.button("Generate Questions", type='primary'):
                to_generate = True

    if to_generate is True:
        # TODO call function to process file
        print('calling file processor to process file')
        process_file("test")
        with st.container(horizontal_alignment='center'):
            st.write("<div style='text-align: center'>success</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader('Loaded Documents')
    st.caption('List of validated and processed document list should appear here')

if not check_credentials():  
    st.stop()

if st.session_state["role"] == "admin":
    doc_panel()
    get_side_bar()              