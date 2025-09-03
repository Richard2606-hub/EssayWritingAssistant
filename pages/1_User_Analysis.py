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

# --- Page Header ---
st.title("🔍 User Analysis")
st.write("Upload your essay to receive **instant feedback** on your strengths, weaknesses, and writing style.")

# --- Model Setup (SPM-focused later) ---
get_genai_connection()
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction = (
        You are an SPM English Paper 2 writing coach.

TASK
- Analyse the learner’s writing (text/doc/pdf/image OCR) against SPM Paper 2 expectations.
- Report strengths and weaknesses that a secondary-school student can act on.
- Identify likely writing_style (Narrative | Descriptive | Expository | Argumentative | Email | Mixed).
- Give a motivating game_like_role (fun nickname).
- If possible, estimate indicative component scores using FOUR lenses, each 0–5:
  content, organization, language, communicative (format/task fulfillment).
- Output JSON ONLY (no code fences).

OUTPUT SCHEMA
{
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "writing_style": "Narrative | Descriptive | Expository | Argumentative | Email | Mixed",
  "game_like_role": "The Persuader",
  "indicative_scores": {
    "content": 0-5,
    "organization": 0-5,
    "language": 0-5,
    "communicative": 0-5,
    "total_out_of_20": 0-20
  },
  "top_priorities": ["short, concrete actions, max 3"]
}

GUIDANCE (for the model)
- CONTENT: relevance, coverage of prompts/notes, idea development.
- ORGANIZATION: paragraphing, sequencing, cohesion/linkers.
- LANGUAGE: grammar accuracy, vocabulary range/precision, sentence variety; appropriate tone.
- COMMUNICATIVE: fulfills task & text-type conventions (e.g., email greeting/closing, report headings, article title).
- Keep bullets short, student-friendly. JSON only.

    )
)

# --- Helper functions ---
def get_user_analysis(files):
    response = model.generate_content(files)
    return response.text

def update_user_info(response_json):
    """Save results into session and DB"""
    st.session_state["user_analysis"] = response_json

    # Save to history (for Objective 3 - progress tracking)
    score = response_json.get("score", None)
    if score is not None:
        history_entry = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "score": score
        }
        if "user_history" not in st.session_state:
            st.session_state["user_history"] = []
        st.session_state["user_history"].append(history_entry)

    # Save into DB if user is logged in
    if "user" in st.session_state:
        user = st.session_state["user"]
        user_analysis_collection = get_collection("user_analysis")
        new_user_info = {
            "username": user["username"],
            "user_info": response_json,
            "date": datetime.datetime.now(tz=datetime.timezone.utc),
        }
        user_analysis_collection.insert_one(new_user_info)

# --- File Upload ---
uploaded_files = st.file_uploader(
    "📂 Upload your essay file (txt, docx, pdf, or image)",
    type=["jpg", "jpeg", "png", "txt", "doc", "docx", "pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🔎 Analyze My Writing"):
        files = []
        for file in uploaded_files:
            file_content, file_type = read_file_content(file)
            if file_type != "unsupported":
                files.append(file_content)
            else:
                st.error(f"❌ Unsupported file type: {file.name}")

        # --- AI Analysis ---
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

# --- Display Results ---
if "user_analysis" in st.session_state:
    st.success("✅ Analysis complete! Here’s your feedback:")
    display_user_analysis(st.session_state["user_analysis"])
