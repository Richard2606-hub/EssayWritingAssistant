# Home.py
import streamlit as st

st.set_page_config(page_title="WriteSamrt: Your Personalised Essay Writing Assistant", page_icon="🏠")

st.write("# Welcome to the WriteSmart! 📝")

st.write("You can have your evaluation with these features:")

col1, col2 = st.columns(2)

with col1:
    if st.button("User Analysis", use_container_width=True):
        st.switch_page("pages/1_User_Analysis.py")
    
    if st.button("Essay Suggestion", use_container_width=True):
        st.switch_page("pages/2_Essay_Suggestion.py")

with col2:
    if st.button("Essay Writing Chat", use_container_width=True):
        st.switch_page("pages/3_Essay_Writing_Chat.py")

    if st.button("Self Analysis", use_container_width=True):
        st.switch_page("pages/4_Self_Analysis.py")
