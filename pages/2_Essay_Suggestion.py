# pages/2_Essay_Suggestion.py
import os, sys, json
import streamlit as st
from datetime import datetime
import google.generativeai as genai

st.set_page_config(page_title="Essay Suggestion", page_icon="💡", layout="wide")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from File_handling import read_file_content
from Connection import get_collection, get_genai_connection
from Data_Visualization import display_suggestion

st.title("💡 Essay Suggestions")
st.write("Upload your essay to receive **SPM-style scoring**, plus concrete sentence-level improvements.")

get_genai_connection()

SYSTEM = (
    "You are an SPM English Paper 2 examiner.\n"
    "TASK\n"
    "1) Detect the part: 'Part 1' (Email), 'Part 2' (Guided Essay), or 'Part 3' (Extended Writing).\n"
    "2) Detect essay type (Narrative | Descriptive | Expository | Argumentative | Email | Article | Report | Review).\n"
    "3) Score FOUR lenses (0–5 each): content, organization, language, communicative (format/task fulfillment). Sum to total_out_of_20.\n"
    "4) Provide 3–6 targeted improvements with:\n"
    "   - original_text (short quote),\n"
    "   - suggestion (what & why),\n"
    "   - improved_version (your rewrite).\n"
    "OUTPUT JSON ONLY (no code fences).\n\n"
    "OUTPUT\n"
    "{\n"
    '  "part": "Part 1 | Part 2 | Part 3",\n'
    '  "essay_evaluation": {\n'
    '    "type_of_essay": "Narrative | Descriptive | Expository | Argumentative | Email | Article | Report | Review",\n'
    '    "scores": {\n'
    '      "content": 0-5, "organization": 0-5, "language": 0-5, "communicative": 0-5, "total_out_of_20": 0-20\n'
    "    },\n"
    '    "feedback": [\n'
    '      {"section": 1, "original_text": "...", "suggestion": "...", "improved_version": "..." }\n'
    "    ]\n"
    "  }\n"
    "}\n"
    "STYLE: secondary school friendly; concise; exam-focused."
)

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM)

def _safe_parse_json(raw_text: str):
    start, end = raw_text.find("{"), raw_text.rfind("}") + 1
    if start == -1 or end <= 0: return None
    try: return json.loads(raw_text[start:end])
    except Exception: return None

def add_to_collection(data):
    get_collection("user_performance").insert_one(data)

uploaded_file = st.file_uploader(
    "📂 Upload your essay (txt/docx/pdf)",
    type=["txt", "doc", "docx", "pdf"]
)

if uploaded_file:
    essay_content, ftype = read_file_content(uploaded_file)
    if ftype == "unsupported":
        st.error("❌ Unsupported file"); st.stop()

    with st.expander("📖 View Uploaded Essay"):
        st.markdown(f"```text\n{essay_content}\n```")

    if st.button("✨ Get Suggestions"):
        with st.spinner("Analyzing your essay..."):
            raw = model.generate_content([essay_content, json.dumps(st.session_state.get("user_info",{}))]).text
            data = _safe_parse_json(raw)
            if not data:
                st.error("⚠️ Could not parse AI response."); st.stop()

            # Safety: compute total if missing
            eval_data = data.get("essay_evaluation", {})
            scores = eval_data.get("scores", {})
            need = ["content","organization","language","communicative"]
            if "total_out_of_20" not in scores and all(k in scores for k in need):
                try:
                    scores["total_out_of_20"] = int(
                        scores["content"] + scores["organization"] + scores["language"] + scores["communicative"]
                    )
                    eval_data["scores"] = scores
                    data["essay_evaluation"] = eval_data
                except Exception:
                    pass

            st.session_state["essay_suggestions"] = data

            if "user" in st.session_state:
                add_to_collection({
                    "username": st.session_state["user"]["username"],
                    "suggestions": data,
                    "timestamp": datetime.now()
                })

if "essay_suggestions" in st.session_state:
    st.success("✅ Analysis complete! Scroll for details.")
    # Normalize to the structure expected by display_suggestion()
    # (wrapper converts 'essay_evaluation' to 'essay_score' key name for compatibility)
    d = st.session_state["essay_suggestions"]
    wrapped = {
        "essay_score": {
            "type_of_essay": d.get("essay_evaluation", {}).get("type_of_essay", "—"),
            "scores": d.get("essay_evaluation", {}).get("scores", {}),
            "essay_suggestion": d.get("essay_evaluation", {}).get("feedback", [])
        }
    }
    display_suggestion(wrapped)
