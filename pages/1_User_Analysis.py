import json
import os
import sys
import datetime
import streamlit as st
import google.generativeai as genai
from File_handling import read_file_content
from Connection import get_collection, get_genai_connection
from Data_Visualization import display_user_analysis

# --- Page Config ---
st.set_page_config(page_title="User Analysis", page_icon="🔍", layout="wide")

# --- Custom Style ---
st.markdown("""
    <style>
      .hero { text-align:center; margin-top:0.5rem; }
      .hero h1 { font-size: 2rem; color:#2E86C1; }
      .hero p { font-size: 1rem; color:#117864; }
      .upload-card { background:#F8F9F9; padding:1rem; border-radius:14px;
                     box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-top:1rem; }
      .stButton>button { width:100%; height:50px; border-radius:10px; font-size:1rem;
                         font-weight:600; background:#2E86C1; color:white; border:none; }
      .stButton>button:hover { background:#1B4F72; }
    </style>
""", unsafe_allow_html=True)

# --- Title Section ---
st.markdown('<div class="hero"><h1>🔍 User Analysis</h1><p>Upload your essay to discover your strengths, weaknesses, and writing style.</p></div>', unsafe_allow_html=True)
st.write("---")

# --- Setup model ---
get_genai_connection()
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=(
        "You are a teacher who helps learners improve their essay writing. "
        "The learner uploads an essay (text, doc, or image). "
        "You must give feedback in JSON with: strengths, weaknesses, writing_style, game_like_role. "
        "Types of writing_style: narrative, argumentative, expository, persuasive.\n"
        "Example: { 'strengths':['Good grammar'], 'weaknesses':['Weak conclusion'], 'writing_style':'Argumentative', 'game_like_role':'The Persuader' }"
    )
)

def get_user_analysis(files):
    response = model.generate_content(files)
    return response.text

def update_user_info(response):
    st.session_state["user_analysis"] = response
    if "user" not in st.session_state:
        return
    user = st.session_state["user"]
    user_analysis_collection = get_collection("user_analysis")
    new_user_info = {
        "username": user["username"],
        "user_info": response,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    user_analysis_collection.insert_one(new_user_info)

# --- Upload Section ---
with st.container():
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "📂 Upload your essay files (txt, docx, pdf, image)...",
        type=["jpg", "jpeg", "png", "txt", "doc", "docx", "pdf"],
        accept_multiple_files=True
    )
    if uploaded_files and st.button("🔎 Analyze My Writing"):
        files = []
        for file in uploaded_files:
            file_content, file_type = read_file_content(file)
            if file_type != "unsupported":
                files.append(file_content)
            else:
                st.error(f"❌ Unsupported file type: {file.name}")

        # Keep retrying until JSON is valid
        invalid_json = True
        while invalid_json:
            with st.spinner("Analyzing your essay... please wait ⏳"):
                response = get_user_analysis(files)
                start = response.find('{')
                end = response.rfind('}') + 1
                response = response[start:end]
            try:
                response_json = json.loads(response)
                invalid_json = False
            except json.JSONDecodeError:
                pass

        update_user_info(response_json)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Display Section ---
if "user_analysis" in st.session_state:
    st.success("✅ Analysis complete! Here’s your feedback:")
    display_user_analysis(st.session_state["user_analysis"])
