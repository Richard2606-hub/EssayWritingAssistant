# pages/2_Essay_Suggestion.py
import os, sys, json
from datetime import datetime
import streamlit as st
import google.generativeai as genai

# --- Page Config ---
st.set_page_config(page_title="Essay Suggestion", page_icon="💡", layout="wide")

# --- Local imports ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection, get_genai_connection
from File_handling import read_file_content

st.title("💡 Essay Suggestions (SPM Paper 2)")
st.markdown(
    """
    Upload your essay and get **SPM-style scoring & targeted improvements**.  
    You’ll see **4 lenses (0–5)** → **total /20**, plus concrete rewrites.
    """
)

# --- AI Setup ---
get_genai_connection()

SYSTEM_PROMPT = (
    "You are a strict but encouraging **SPM English Paper 2 examiner**. "
    "You will receive a student essay (text/docx/pdf/image OCR) and optional student profile. "
    "Return **JSON ONLY** (no code fences). Keep feedback short, clear, exam-focused.\n\n"

    "DETECTION\n"
    "- Detect the likely Part (Part 1 Email | Part 2 Guided Essay | Part 3 Extended Writing).\n"
    "- Detect the text type (Narrative | Descriptive | Expository | Argumentative | Email | Article | Report | Review | Mixed).\n\n"

    "SCORING RUBRIC (0–5 per lens; integers only)\n"
    "CONTENT (relevance, coverage, idea development)\n"
    "  0: Off-task/irrelevant | 1: Barely addresses; very thin\n"
    "  2: Partly relevant; ≥1 required point missing/misinterpreted; thin; generic examples\n"
    "  3: Generally addresses; some development; minor omissions\n"
    "  4: All points present; mostly well developed; minor lapses; relevant examples\n"
    "  5: Fully relevant; well-developed ideas with apt examples\n"
    "ORGANIZATION (paragraphing, sequencing, cohesion)\n"
    "  0: No clear structure | 1: Minimal paragraphing; poor flow\n"
    "  2: Weak structure; abrupt jumps; limited devices; sequence sometimes confusing\n"
    "  3: Logical sequence; basic cohesion; some weak links\n"
    "  4: Clear structure; mostly smooth transitions; occasional slips\n"
    "  5: Clear intro/body/end; smooth, cohesive devices used well\n"
    "LANGUAGE (accuracy, range, sentence variety, tone/register)\n"
    "  0: Very frequent errors; hard to understand | 1: Many basic errors; meaning often unclear\n"
    "  2: Frequent errors sometimes impede meaning; basic/repetitive sentences; limited vocabulary\n"
    "  3: Mostly accurate; some slips; adequate range\n"
    "  4: Generally accurate; minor slips; some variety; mostly apt vocabulary/register\n"
    "  5: Accurate, varied, effective word choice; appropriate tone\n"
    "COMMUNICATIVE (task fulfilment & genre/format conventions)\n"
    "  0: Wrong/ignored task | 1: Major format/tone issues; notes not covered\n"
    "  2: Partly achieved; several notes missing/wrong; tone often off; key format missing\n"
    "  3: Mostly achieved; basic format present; minor omissions\n"
    "  4: Achieved; all notes addressed (one may be shallow); tone appropriate; format mostly correct\n"
    "  5: Fully achieved; all requirements met; strong genre conventions\n\n"

    "OUTPUT JSON SCHEMA (STRICT)\n"
    "{\n"
    '  "essay_evaluation": {\n'
    '    "part": "Part 1 | Part 2 | Part 3",\n'
    '    "type_of_essay": "Narrative | Descriptive | Expository | Argumentative | Email | Article | Report | Review | Mixed",\n'
    '    "scores": {\n'
    '      "content": 0-5,\n'
    '      "organization": 0-5,\n'
    '      "language": 0-5,\n'
    '      "communicative": 0-5,\n'
    '      "total_out_of_20": 0-20\n'
    "    },\n"
    '    "feedback": [\n'
    '      {\n'
    '        "section": 1,\n'
    '        "original_text": "short quote or sentence",\n'
    '        "issue": "what’s wrong",\n'
    '        "suggestion": "what to do",\n'
    '        "improved_version": "short corrected/improved version"\n'
    "      }\n"
    "    ],\n"
    '    "summary_comment": "2–3 sentences summing up strengths/weaknesses",\n'
    '    "next_focus": ["3 concrete actions e.g., Use signposting transitions.", "...", "..."]\n'
    "  }\n"
    "}\n\n"
    "RULES\n"
    "- Return JSON ONLY (no markdown). Short, student-friendly bullets. "
    "- If unsure, choose nearest integer level for each lens."
)

model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)

# --- Helpers ---
def _safe_parse_json(raw_text: str):
    s, e = raw_text.find("{"), raw_text.rfind("}") + 1
    if s == -1 or e <= 0:
        return None
    try:
        return json.loads(raw_text[s:e])
    except Exception:
        return None

def _coerce_0_5(x):
    try:
        v = int(round(float(x)))
        return max(0, min(5, v))
    except Exception:
        return None

def _fix_scores(scores: dict) -> dict:
    if not isinstance(scores, dict):
        return {}
    out = {}
    for k in ["content", "organization", "language", "communicative"]:
        out[k] = _coerce_0_5(scores.get(k))
    if all(v is not None for v in out.values()):
        try:
            total = scores.get("total_out_of_20")
            total = int(total) if total is not None else sum(out.values())
        except Exception:
            total = sum(out.values())
        out["total_out_of_20"] = max(0, min(20, int(total)))
    return out

def add_to_collection(data):
    get_collection("user_performance").insert_one(data)

# --- Upload ---
uploaded_file = st.file_uploader(
    "📂 Upload your essay (txt, docx, pdf, or image)",
    type=["txt", "doc", "docx", "pdf", "jpg", "jpeg", "png"]
)

if uploaded_file:
    essay_content, file_type = read_file_content(uploaded_file)
    if file_type == "unsupported":
        st.error("❌ Unsupported file type")
        st.stop()

    with st.expander("📖 View Uploaded Essay / Image Preview"):
        if isinstance(essay_content, str):
            st.markdown(f"```text\n{essay_content[:500]}\n```")
        else:
            st.image(essay_content, caption="Uploaded image")

    if st.button("✨ Get Suggestions"):
        student_profile = st.session_state.get("user_info", {})
        userinfo = json.dumps(student_profile) if isinstance(student_profile, dict) else str(student_profile)

        with st.spinner("Analyzing your essay... ⏳"):
            try:
                response = model.generate_content([essay_content, userinfo]).text
            except Exception as e:
                st.error(f"Model error: {e}")
                st.stop()

        data = _safe_parse_json(response)
        if not data:
            st.error("⚠️ Could not parse AI response. Please try again.")
            st.stop()

        eval_data = data.get("essay_evaluation", {})
        eval_data.setdefault("scores", {})
        eval_data["scores"] = _fix_scores(eval_data["scores"])

        st.session_state["essay_suggestions"] = {"essay_evaluation": eval_data}

        # Save if logged in
        if "user" in st.session_state:
            add_to_collection({
                "username": st.session_state["user"]["username"],
                "suggestions": st.session_state["essay_suggestions"],
                "timestamp": datetime.now()
            })

# --- Display ---
if "essay_suggestions" in st.session_state:
    data = st.session_state["essay_suggestions"]
    eval_data = data.get("essay_evaluation", {})
    scores = eval_data.get("scores", {})
    feedback = eval_data.get("feedback", [])
    part = eval_data.get("part", "—")
    essay_type = eval_data.get("type_of_essay", "Unknown")

    st.success("✅ Analysis complete! Here are your suggestions:")
    st.subheader("🧭 Detected Task")
    st.write(f"**Part:** {part}  |  **Type:** {essay_type}")

    # Metrics for 4 lenses
    st.subheader("⭐ Scores (SPM, out of 5 each → total /20)")
    cols = st.columns(5)
    lens_order = ["content", "organization", "language", "communicative", "total_out_of_20"]
    labels = {
        "content": "Content",
        "organization": "Organization",
        "language": "Language",
        "communicative": "Communicative",
        "total_out_of_20": "Total (/20)"
    }
    for i, k in enumerate(lens_order):
        with cols[i]:
            v = scores.get(k, "—")
            st.metric(label=labels[k], value=v)

    st.subheader("💬 Suggestions & Improvements")
    if feedback:
        for f in feedback:
            with st.expander(f"Section {f.get('section','?')}"):
                st.markdown(
                    f"- 📌 **Original:** *{f.get('original_text','')}*\n"
                    f"- ⚠️ **Issue:** {f.get('issue','')}\n"
                    f"- 💡 **Suggestion:** {f.get('suggestion','')}\n"
                    f"- ✨ **Improved:** **{f.get('improved_version','')}**"
                )
    else:
        st.info("No granular feedback provided.")

    if eval_data.get("summary_comment"):
        st.subheader("📝 Summary")
        st.write(eval_data["summary_comment"])

    if eval_data.get("next_focus"):
        st.subheader("🎯 Next Focus")
        for tip in eval_data["next_focus"]:
            st.write(f"- {tip}")
