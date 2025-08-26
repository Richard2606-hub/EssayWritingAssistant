import sys
import os
import json
import streamlit as st
from datetime import datetime
import google.generativeai as genai
from File_handling import read_file_content
from Connection import get_collection, get_genai_connection
from Data_Visualization import display_suggestion

# --- Page Config ---
st.set_page_config(page_title="Essay Suggestion", page_icon="💡", layout="wide")

# --- Page Header ---
st.title("💡 Essay Suggestions")
st.markdown(
    """
    Upload your essay and receive **SPM-style feedback** 🎓  
    Our AI will score your work and give you practical suggestions to improve.  
    """
)

# --- AI Connection ---
get_genai_connection()

def get_essay_suggestions(essay, userinfo):
    """Send essay + user info to AI model and return structured JSON feedback"""

    system_prompt = (
        "You are an SPM English examiner. You will be given an essay and the student's "
        "strengths and weaknesses. \n"
        "1. Score the essay (0–10) based on **SPM criteria**: Content, Organization, Language. \n"
        "2. Provide **specific suggestions** with improved versions of weak sentences. \n"
        "3. Output must be JSON format only. Example:\n"
        "{\n"
        "  'essay_evaluation': {\n"
        "    'type_of_essay': 'Narrative Essay',\n"
        "    'scores': {\n"
        "       'content': 6,\n"
        "       'organization': 5,\n"
        "       'language': 7,\n"
        "       'overall_score': 6\n"
        "    },\n"
        "    'feedback': [\n"
        "      {\n"
        "        'section': 1,\n"
        "        'original_text': 'Original sentence...',\n"
        "        'suggestion': 'Be more specific',\n"
        "        'improved_version': 'Improved sentence here...'\n"
        "      }\n"
        "    ]\n"
        "  }\n"
        "}"
    )

    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=system_prompt
    )

    response = model.generate_content([essay, userinfo])

    # Extract JSON safely
    raw_text = response.text
    start, end = raw_text.find("{"), raw_text.rfind("}") + 1
    cleaned = raw_text[start:end]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        st.error("⚠️ Could not parse AI response. Please try again.")
        return None

# --- Save to DB ---
def add_to_collection(data):
    collection = get_collection("user_performance")
    collection.insert_one(data)

# --- File Upload ---
uploaded_file = st.file_uploader(
    "📂 Upload your essay (txt, docx, pdf)",
    type=["txt", "doc", "docx", "pdf"]
)

if uploaded_file:
    essay_content, file_type = read_file_content(uploaded_file)
    if file_type == "unsupported":
        st.error("❌ Unsupported file type")
        st.stop()

    with st.expander("📖 View Uploaded Essay"):
        st.markdown(f"```text\n{essay_content}\n```")

    if st.button("✨ Get Suggestions"):
        user_info = st.session_state.get("user_info", "")

        with st.spinner("Analyzing your essay... ⏳"):
            suggestions_json = get_essay_suggestions(essay_content, user_info)

        if suggestions_json:
            st.session_state["essay_suggestions"] = suggestions_json

            # Save to DB if logged in
            if "user" in st.session_state:
                user = st.session_state["user"]
                add_to_collection({
                    "username": user["username"],
                    "suggestions": suggestions_json,
                    "timestamp": datetime.now()
                })

# --- Display Suggestions ---
if "essay_suggestions" in st.session_state:
    data = st.session_state["essay_suggestions"]

    st.success("✅ Analysis complete! Here are your suggestions:")

    eval_data = data.get("essay_evaluation", {})
    scores = eval_data.get("scores", {})
    feedback = eval_data.get("feedback", [])

    # Show scores
    st.subheader("⭐ Essay Scores (SPM Criteria)")
    cols = st.columns(len(scores))
    for i, (crit, val) in enumerate(scores.items()):
        with cols[i]:
            st.metric(label=crit.capitalize(), value=val)

    # Show type of essay
    st.info(f"📝 Type of Essay Detected: **{eval_data.get('type_of_essay', 'Unknown')}**")

    # Suggestions Section
    st.subheader("💬 Suggestions & Improvements")
    for f in feedback:
        st.markdown(
            f"""
            **Section {f.get('section')}**
            - 📌 Original: *{f.get('original_text')}*  
            - 💡 Suggestion: {f.get('suggestion')}  
            - ✨ Improved: **{f.get('improved_version')}**
            """
        )
