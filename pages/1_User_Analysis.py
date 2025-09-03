# pages/1_User_Analysis.py
import os, sys, json, datetime
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="User Analysis", page_icon="🔍", layout="wide")

# local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection, get_genai_connection
from File_handling import read_file_content
from Data_Visualization import display_user_analysis

st.title("🔍 User Analysis (SPM Paper 2)")
st.write("Upload your essay to get **SPM-style feedback**: strengths, weaknesses, writing style, and indicative scores.")

# ---------------------------
#  Model & Prompt
# ---------------------------
get_genai_connection()

SYSTEM_PROMPT = (
    "You are an experienced **SPM English Paper 2** examiner and teacher for secondary school students.\n"
    "You receive ONE learner essay (text, PDF, DOCX, or image OCR). Analyse it and return **JSON ONLY** (no code fences).\n\n"
    "SCOPE & TONE\n"
    "- Target audience: Form 4–5 students. Keep feedback friendly, direct, and exam-practical.\n"
    "- Detect/confirm text type: Narrative | Descriptive | Expository | Argumentative | Email | Article | Report | Review | Mixed.\n"
    "- If format conventions are missing (e.g., email greeting/closing), reflect that under **communicative**.\n\n"
    "MARKING LENSES (0–5 each)\n"
    "Use these consistent descriptors. If uncertain, pick the nearest level.\n"
    "CONTENT (relevance, coverage, idea development)\n"
    "  0: Off-task/very little relevant content | 1: Barely addresses task; ideas very thin\n"
    "  2: Partly relevant; ≥1 required point missing/misinterpreted; ideas listed; development thin; generic examples\n"
    "  3: Generally addresses task; some development; minor omissions\n"
    "  4: All required points present; mostly well developed; minor lapses only; examples mostly relevant\n"
    "  5: Fully relevant; covers required points; clear, well-developed ideas with apt examples\n"
    "ORGANIZATION (paragraphing, sequencing, cohesion)\n"
    "  0: No clear structure | 1: Minimal paragraphing; poor flow\n"
    "  2: Weak structure; inconsistent paragraphing; abrupt jumps; limited devices; sequence sometimes confusing\n"
    "  3: Logical sequencing; basic cohesion; some weak links\n"
    "  4: Clear overall structure (intro/body/ending); mostly smooth flow; appropriate transitions; occasional slips\n"
    "  5: Clear intro/body/ending; smooth flow; cohesive devices well used\n"
    "LANGUAGE (accuracy, range, sentence variety, tone/register)\n"
    "  0: Very frequent errors; hard to understand | 1: Many basic errors; meaning often unclear\n"
    "  2: Frequent errors sometimes impede meaning; basic/repetitive sentences; limited vocabulary; occasional wrong word choice\n"
    "  3: Mostly accurate; some slips; adequate range\n"
    "  4: Generally accurate; errors minor and do not hinder meaning; some sentence variety; mostly apt vocabulary/register\n"
    "  5: Accurate and varied; effective word choice; appropriate tone\n"
    "COMMUNICATIVE (task fulfilment & format/genre conventions)\n"
    "  0: Task not attempted/ignored; wrong genre | 1: Major format/tone issues; notes not covered\n"
    "  2: Task partly achieved; several notes unaddressed or wrongly tackled; tone/audience often off; key format elements missing\n"
    "  3: Task mostly achieved; basic format present; minor omissions\n"
    "  4: Task achieved; all notes addressed (one may be shallow); tone/audience appropriate; format/genre mostly correct\n"
    "  5: Task fully achieved; all notes/requirements met; genre conventions clear and effective\n\n"
    "SCORING HINTS (quick reference 0–5 for each lens)\n"
    "- CONTENT:\n"
    "  0 Off-task/irrelevant | 1 Barely addresses; very thin | 2 Partly relevant; ≥1 point missing | 3 Generally addresses; some development | 4 All points; mostly developed | 5 Fully relevant; well-developed ideas\n"
    "- ORGANIZATION:\n"
    "  0 No structure | 1 Minimal paragraphing; poor flow | 2 Weak structure; abrupt jumps | 3 Logical sequence; basic cohesion | 4 Clear structure; mostly smooth | 5 Clear intro/body/end; smooth, cohesive\n"
    "- LANGUAGE:\n"
    "  0 Very frequent errors; hard to follow | 1 Many basic errors; meaning often unclear | 2 Errors sometimes impede meaning; basic/repetitive; limited vocab | 3 Mostly accurate; some slips; adequate range | 4 Generally accurate; minor slips; some variety; apt vocab | 5 Accurate, varied, effective word choice; appropriate tone\n"
    "- COMMUNICATIVE:\n"
    "  0 Wrong/ignored task | 1 Major format/tone issues; notes not covered | 2 Partly achieved; several notes missing; tone off; key format missing | 3 Mostly achieved; basic format; minor omissions | 4 Achieved; all notes addressed; appropriate tone; format mostly correct | 5 Fully achieved; all requirements; strong genre conventions\n\n"
    "OUTPUT JSON SCHEMA (STRICT)\n"
    "{\n"
    '  "strengths": ["short, student-friendly bullet", "..."],\n'
    '  "weaknesses": ["short, student-friendly bullet", "..."],\n'
    '  "writing_style": "Narrative | Descriptive | Expository | Argumentative | Email | Article | Report | Review | Mixed",\n'
    '  "game_like_role": "A motivating nickname, e.g., The Persuader",\n'
    '  "indicative_scores": {\n'
    '    "content": 0-5,\n'
    '    "organization": 0-5,\n'
    '    "language": 0-5,\n'
    '    "communicative": 0-5,\n'
    '    "total_out_of_20": 0-20\n'
    "  },\n"
    '  "top_priorities": ["3 short actions the student can do next, e.g., Use signposting transitions like Firstly/Next/Finally.", "...", "..."]\n'
    "}\n\n"
    "RULES\n"
    "- Return JSON ONLY (no markdown, no commentary).\n"
    "- Keep bullets concise; avoid re-writing the whole essay here.\n"
    "- If unsure of a lens, choose the nearest integer level.\n"
)

model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# ---------------------------
#  Helpers
# ---------------------------
def _safe_parse_json(raw_text: str):
    start, end = raw_text.find("{"), raw_text.rfind("}") + 1
    if start == -1 or end <= 0:
        return None
    try:
        return json.loads(raw_text[start:end])
    except Exception:
        return None

def _coerce_0_5(x):
    try:
        v = int(round(float(x)))
        return max(0, min(5, v))
    except Exception:
        return None

def _coerce_scores(d: dict) -> dict:
    """
    Ensure scores are ints in [0,5] and compute total_out_of_20 if missing.
    """
    if not isinstance(d, dict):
        return {}
    out = {}
    for k in ["content", "organization", "language", "communicative"]:
        out[k] = _coerce_0_5(d.get(k))
    # compute total if we have all 4
    if all(v is not None for v in out.values()):
        try:
            total = d.get("total_out_of_20")
            total = int(total) if total is not None else sum(out.values())
        except Exception:
            total = sum(out.values())
        out["total_out_of_20"] = max(0, min(20, int(total)))
    return out

def update_user_info(response_json):
    st.session_state["user_analysis"] = response_json
    if "user" in st.session_state:
        get_collection("user_analysis").insert_one({
            "username": st.session_state["user"]["username"],
            "user_info": response_json,
            "date": datetime.datetime.now(tz=datetime.timezone.utc),
        })

# ---------------------------
#  UI
# ---------------------------
uploaded_files = st.file_uploader(
    "📂 Upload text/docx/pdf/image",
    type=["jpg","jpeg","png","txt","doc","docx","pdf"],
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
        try:
            raw = model.generate_content(files).text
        except Exception as e:
            st.error(f"Model error: {e}")
            st.stop()

        data = _safe_parse_json(raw)
        if not data:
            st.error("⚠️ Could not parse response. Please try again.")
            st.stop()

        # Ensure required keys exist
        data.setdefault("strengths", [])
        data.setdefault("weaknesses", [])
        data.setdefault("writing_style", "Mixed")
        data.setdefault("game_like_role", "The Builder")
        data.setdefault("indicative_scores", {})
        data.setdefault("top_priorities", [])

        # Coerce scores and compute total
        data["indicative_scores"] = _coerce_scores(data.get("indicative_scores", {}))

        update_user_info(data)

if "user_analysis" in st.session_state:
    st.success("✅ Analysis complete! Here’s your feedback:")
    display_user_analysis(st.session_state["user_analysis"])
