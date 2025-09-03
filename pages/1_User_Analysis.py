# pages/1_User_Analysis.py
import os, sys, json, datetime
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="User Analysis", page_icon="🔍", layout="wide")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection, get_genai_connection
from File_handling import read_file_content
from Data_Visualization import display_user_analysis

st.title("🔍 User Analysis")
st.write("Upload your essay to get feedback aligned to **SPM Paper 2**.")

get_genai_connection()
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=(
        "You are an SPM English Paper 2 writing coach.\n"
        "TASK\n"
        "- Analyse the learner’s writing (text/doc/pdf/image OCR) against SPM Paper 2 expectations.\n"
        "- Provide strengths and weaknesses that are actionable for secondary school students.\n"
        "- Identify writing_style (Narrative | Descriptive | Expository | Argumentative | Email | Mixed).\n"
        "- Give a motivating game_like_role.\n"
        "- If possible, estimate indicative component scores using FOUR lenses (0–5 each): content, organization, language, communicative.\n"
        "- Sum to total_out_of_20.\n"
        "- Output JSON ONLY (no code fences).\n\n"
        "OUTPUT SCHEMA\n"
        "{\n"
        '  "strengths": ["...", "..."],\n'
        '  "weaknesses": ["...", "..."],\n'
        '  "writing_style": "Narrative | Descriptive | Expository | Argumentative | Email | Mixed",\n'
        '  "game_like_role": "The Persuader",\n'
        '  "indicative_scores": {\n'
        '    "content": 0-5, "organization": 0-5, "language": 0-5, "communicative": 0-5,\n'
        '    "total_out_of_20": 0-20\n'
        "  },\n"
        '  "top_priorities": ["short, concrete actions, max 3"]\n'
        "}\n"
        "RULES: JSON only."
    )
)

def _safe_parse_json(raw_text: str):
    start, end = raw_text.find("{"), raw_text.rfind("}") + 1
    if start == -1 or end <= 0: return None
    try: return json.loads(raw_text[start:end])
    except Exception: return None

def update_user_info(response_json):
    st.session_state["user_analysis"] = response_json
    if "user" in st.session_state:
        user = st.session_state["user"]
        get_collection("user_analysis").insert_one({
            "username": user["username"],
            "user_info": response_json,
            "date": datetime.datetime.now(tz=datetime.timezone.utc),
        })

uploaded_files = st.file_uploader(
    "📂 Upload text/docx/pdf/image",
    type=["jpg", "jpeg", "png", "txt", "doc", "docx", "pdf"],
    accept_multiple_files=True
)

if uploaded_files and st.button("🔎 Analyze My Writing"):
    files = []
    for file in uploaded_files:
        content, ftype = read_file_content(file)
        if ftype == "unsupported":
            st.error(f"❌ Unsupported file: {file.name}")
        else:
            files.append(content)

    with st.spinner("Analyzing..."):
        raw = model.generate_content(files).text
        js = _safe_parse_json(raw)
        if not js:
            st.error("⚠️ Could not parse response. Try again.")
        else:
            indic = js.get("indicative_scores", {})
            need = ["content","organization","language","communicative"]
            if "total_out_of_20" not in indic and all(k in indic for k in need):
                try:
                    indic["total_out_of_20"] = int(
                        indic["content"] + indic["organization"] + indic["language"] + indic["communicative"]
                    )
                    js["indicative_scores"] = indic
                except Exception:
                    pass
            update_user_info(js)

if "user_analysis" in st.session_state:
    st.success("✅ Analysis complete!")
    display_user_analysis(st.session_state["user_analysis"])
