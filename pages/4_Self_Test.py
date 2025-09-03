# pages/4_Self_Test.py
import os
import sys
import json
import time
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# Local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from File_handling import read_file_content
from Connection import get_genai_connection, get_collection

st.set_page_config(page_title="Self-Test 📚", page_icon="📚", layout="wide")

# ---------------------------
#   Page Header
# ---------------------------
st.title("📚 Essay Self-Test (SPM Paper 2)")
st.markdown(
    """
Welcome to the **Self-Test Zone**! ✨  
Choose the **part/type** you want to practise, submit your essay, and get **SPM-style feedback**.

- Scoring uses **4 lenses (0–5 each)** → **Total out of 20**  
- Submit at least **5 essays** to unlock your **progress dashboard**  
"""
)

# ---------------------------
#   Session Storage
# ---------------------------
if "self_test_essays" not in st.session_state:
    st.session_state["self_test_essays"] = []

# Optional: persist to DB (if logged in)
attempts_collection = get_collection("self_test_attempts")

# ---------------------------
#   Model Setup
# ---------------------------
genai_client = get_genai_connection()
MODEL_NAME = "gemini-1.5-flash"

SELF_TEST_SYSTEM = (
    "You are an SPM English Paper 2 examiner providing formative assessment.\n"
    "INPUT: one student essay (text or OCR). You will also receive the intended part/type.\n\n"
    "TASK\n"
    "- Detect/confirm part: 'Part 1' (Email) | 'Part 2' (Guided Essay) | 'Part 3' (Extended Writing).\n"
    "- Detect/confirm type_of_essay where relevant (Narrative | Descriptive | Expository | Argumentative | Article | Report | Review | Email).\n"
    "- Score FOUR lenses (0–5 each): content, organization, language, communicative (format/task fulfillment).\n"
    "- Sum to total_out_of_20 (0–20).\n"
    "- Summarise 2–4 strengths and 2–4 weaknesses.\n"
    "- Provide 3 short next_focus goals (concrete actions, student-friendly).\n"
    "- Output JSON ONLY (no code fences).\n\n"
    "LENSES QUICK HINTS\n"
    "- CONTENT: relevance, coverage of prompts/notes, idea development.\n"
    "- ORGANIZATION: paragraphing, sequencing, cohesion/linkers.\n"
    "- LANGUAGE: accuracy, range/precision, sentence variety, tone.\n"
    "- COMMUNICATIVE: fulfils task & text-type conventions (email greeting/closing, article title, report headings, review evaluative tone, etc.).\n\n"
    "OUTPUT\n"
    "{\n"
    '  "part": "Part 1 | Part 2 | Part 3",\n'
    '  "type_of_essay": "Email | Article | Report | Review | Narrative | Descriptive | Expository | Argumentative",\n'
    '  "scores": {\n'
    '    "content": 0-5,\n'
    '    "organization": 0-5,\n'
    '    "language": 0-5,\n'
    '    "communicative": 0-5,\n'
    '    "total_out_of_20": 0-20\n'
    "  },\n"
    '  "feedback": {\n'
    '    "strengths": ["...", "..."],\n'
    '    "weaknesses": ["...", "..."]\n'
    "  },\n"
    '  "next_focus": ["...", "...", "..."]\n'
    "}\n"
    "RULES: JSON only."
)

model = genai.GenerativeModel(
    MODEL_NAME,
    system_instruction=SELF_TEST_SYSTEM
)

# ---------------------------
#   Practice Prompt Generator
# ---------------------------
PROMPT_GEN_SYSTEM = (
    "You are an SPM Paper 2 prompt writer. Generate one realistic practice task "
    "for the requested part/type. Output JSON ONLY with:\n"
    "{\n"
    '  "title": "...",\n'
    '  "instructions": "...",\n'
    '  "notes": ["note1", "note2", "note3"],\n'
    '  "word_count": "e.g., 80 for Part 1; 125-150 for Part 2; 200-250 for Part 3"\n'
    "}\n"
    "Guidelines:\n"
    "- Part 1 (Email): short email reply; friendly tone; include greeting & closing; about 80 words; include 2–3 notes to respond to.\n"
    "- Part 2 (Guided): include exactly 3 notes; student must use all notes; 125–150 words.\n"
    "- Part 3 (Extended): choose one of Article/Report/Review/Narrative; 200–250 words; ensure appropriate format signals.\n"
    "JSON only."
)
prompt_gen = genai.GenerativeModel(
    MODEL_NAME,
    system_instruction=PROMPT_GEN_SYSTEM
)

def generate_practice_task(selected_part: str, selected_type: str):
    # Compose a short user message for generation
    ask = f"Part: {selected_part}; Type: {selected_type}. Generate one practice task."
    try:
        raw = prompt_gen.generate_content(ask).text
        start, end = raw.find("{"), raw.rfind("}") + 1
        js = json.loads(raw[start:end])
        return js
    except Exception:
        return None

# ---------------------------
#   UI – Choose Part & Type
# ---------------------------
with st.sidebar:
    st.header("🎯 Choose Practice")
    part = st.radio(
        "Select Paper 2 Part",
        options=["Part 1 (Email)", "Part 2 (Guided Essay)", "Part 3 (Extended Writing)"],
        index=0
    )

    subtype = None
    if part == "Part 3 (Extended Writing)":
        subtype = st.selectbox(
            "Choose a type for Part 3",
            options=["Article", "Report", "Review", "Narrative"],
            index=0
        )
    elif part == "Part 1 (Email)":
        subtype = "Email"
    else:
        # Guided essay has no strict subtype beyond general expository/argumentative/etc.,
        # but we'll leave subtype as None and let the model infer.
        subtype = "Guided Essay"

    st.markdown("---")
    if st.button("🎲 Generate a Practice Task"):
        task = generate_practice_task(
            "Part 1" if "Part 1" in part else "Part 2" if "Part 2" in part else "Part 3",
            subtype
        )
        if task:
            st.session_state["last_generated_task"] = task
            st.success("Practice task generated below on the main panel.")
        else:
            st.error("Could not generate a task. Please try again.")

# ---------------------------
#   Show Practice Task (if any)
# ---------------------------
if "last_generated_task" in st.session_state:
    t = st.session_state["last_generated_task"]
    st.markdown("### 🧪 Practice Task")
    st.write(f"**Title:** {t.get('title','—')}")
    st.write(t.get("instructions","—"))
    notes = t.get("notes", [])
    if notes:
        st.write("**Notes (use all):**")
        for i, n in enumerate(notes, 1):
            st.write(f"- {i}. {n}")
    st.caption(f"Suggested length: {t.get('word_count','—')}")

# ---------------------------
#   Input Methods
# ---------------------------
st.markdown("### ✍️ Submit Your Essay")
tabs = st.tabs(["Type Text", "Upload File", "Upload Image"])

essay_text = None

with tabs[0]:
    essay_text = st.text_area(
        "Type or paste your essay here",
        height=220,
        placeholder="Write your essay here…"
    )

with tabs[1]:
    file_u = st.file_uploader(
        "Upload a text/docx/pdf file",
        type=["txt", "doc", "docx", "pdf"],
        key="file_upl"
    )
    if file_u is not None:
        content, ftype = read_file_content(file_u)
        if ftype == "unsupported":
            st.error("❌ Unsupported file type.")
        else:
            st.success(f"Loaded {file_u.name}")
            if isinstance(content, str):
                essay_text = content
            else:
                # In case of image object by mistake
                st.error("This tab expects text/doc/docx/pdf only.")

with tabs[2]:
    img_u = st.file_uploader(
        "Upload an image (jpg/png) of your essay (OCR)",
        type=["jpg", "jpeg", "png"],
        key="img_upl"
    )
    if img_u is not None:
        content, itype = read_file_content(img_u)
        # read_file_content returns PIL.Image for images
        # For Gemini, we can pass the image object directly as a part of content
        essay_text = content  # may be PIL.Image – model can handle multimodal

# ---------------------------
#   Analyze Button
# ---------------------------
col_a, col_b = st.columns([1, 2])
with col_a:
    analyze_clicked = st.button("🔎 Analyze Essay", type="primary", use_container_width=True)
with col_b:
    st.caption("Scoring uses four lenses (0–5 each): Content, Organization, Language, Communicative → Total 20.")

def _safe_parse_json(raw_text: str):
    start, end = raw_text.find("{"), raw_text.rfind("}") + 1
    if start == -1 or end <= 0:
        return None
    try:
        return json.loads(raw_text[start:end])
    except Exception:
        return None

if analyze_clicked:
    if essay_text is None or (isinstance(essay_text, str) and not essay_text.strip()):
        st.error("Please provide your essay (typed, uploaded, or imaged) before analyzing.")
        st.stop()

    with st.spinner("Analyzing essay... ✍️"):
        # Compose a compact control string about selected part/type
        chosen_part = "Part 1" if "Part 1" in part else "Part 2" if "Part 2" in part else "Part 3"
        chosen_type = subtype

        try:
            # Multimodal support: pass text or image directly
            user_payload = []
            if isinstance(essay_text, str):
                user_payload.append(
                    f"Intended part: {chosen_part}\nIntended type: {chosen_type}\n\nESSAY:\n{essay_text}"
                )
            else:
                # PIL image: pass the preamble plus the image
                user_payload.append(
                    f"Intended part: {chosen_part}\nIntended type: {chosen_type}\n\nESSAY (image attached)"
                )
                user_payload.append(essay_text)

            raw = model.generate_content(user_payload).text
        except Exception as e:
            st.error(f"Model error: {e}")
            st.stop()

        analysis_json = _safe_parse_json(raw)
        if not analysis_json:
            st.error("⚠️ Could not parse AI response. Please try again.")
            st.stop()

        # Ensure scoring keys and fill total if missing
        scores = analysis_json.get("scores", analysis_json.get("analysis", {}).get("scores", {}))
        if not scores:
            scores = {}
            analysis_json["scores"] = scores

        need = ["content", "organization", "language", "communicative"]
        if "total_out_of_20" not in scores and all(k in scores for k in need):
            try:
                scores["total_out_of_20"] = int(
                    float(scores["content"]) +
                    float(scores["organization"]) +
                    float(scores["language"]) +
                    float(scores["communicative"])
                )
            except Exception:
                pass

        # Save attempt (session)
        preview = ""
        if isinstance(essay_text, str):
            preview = (essay_text[:300] + "…") if len(essay_text) > 300 else essay_text
        else:
            preview = "[Image Essay Submission]"

        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "part": analysis_json.get("part", chosen_part),
            "type_of_essay": analysis_json.get("type_of_essay", chosen_type),
            "scores": scores,
            "feedback": analysis_json.get("feedback", {}),
            "next_focus": analysis_json.get("next_focus", []),
            "essay_preview": preview
        }
        st.session_state["self_test_essays"].append(record)

        # Save to DB if logged in
        if "user" in st.session_state:
            try:
                user = st.session_state["user"]
                attempts_collection.insert_one({
                    "username": user["username"],
                    "attempt": record,
                    "timestamp": datetime.utcnow()
                })
            except Exception:
                pass

        st.success("✅ Essay analyzed and saved below!")

# ---------------------------
#   Attempts List
# ---------------------------
attempts = st.session_state["self_test_essays"]
num_essays = len(attempts)
st.progress(min(num_essays, 5) / 5)
st.write(f"📌 You have submitted **{num_essays}/5** essays.")

if num_essays > 0:
    st.subheader("📄 Your Attempts")
    for i, e in enumerate(reversed(attempts), 1):
        with st.expander(f"Attempt {num_essays - i + 1} • {e['date']} • {e['part']} • {e.get('type_of_essay','—')}"):
            st.write("**Essay Preview:**")
            st.write(e["essay_preview"] or "—")
            st.write("**Scores (0–5 per lens):**")
            s = e["scores"]
            st.write({
                "Content": s.get("content", None),
                "Organization": s.get("organization", None),
                "Language": s.get("language", None),
                "Communicative": s.get("communicative", None),
                "Total (20)": s.get("total_out_of_20", None)
            })
            fb = e.get("feedback", {})
            if fb:
                st.write("**Strengths:**")
                for x in fb.get("strengths", []):
                    st.write(f"- {x}")
                st.write("**Weaknesses:**")
                for x in fb.get("weaknesses", []):
                    st.write(f"- {x}")
            nf = e.get("next_focus", [])
            if nf:
                st.write("**Next Focus:**")
                for x in nf:
                    st.write(f"- {x}")

# ---------------------------
#   Dashboard (unlocked after 5)
# ---------------------------
if num_essays >= 5:
    st.subheader("📊 Your Progress Dashboard")

    rows = []
    for idx, e in enumerate(attempts, 1):
        s = e.get("scores", {})
        rows.append({
            "Attempt": idx,
            "Part": e.get("part", "—"),
            "Type": e.get("type_of_essay", "—"),
            "Content": s.get("content", None),
            "Organization": s.get("organization", None),
            "Language": s.get("language", None),
            "Communicative": s.get("communicative", None),
            "Total(20)": s.get("total_out_of_20", None)
        })
    df = pd.DataFrame(rows)

    # Trend lines across all attempts
    st.write("### 📈 Lens Trends (0–5 each) & Total(20)")
    plot_cols = ["Content", "Organization", "Language", "Communicative", "Total(20)"]
    fig = px.line(df, x="Attempt", y=plot_cols, markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Average by Type (useful for Part 3 recommendation logic later)
    st.write("### 🧠 Average Scores by Essay Type")
    by_type = df.groupby("Type")[["Content", "Organization", "Language", "Communicative", "Total(20)"]].mean().reset_index()
    st.dataframe(by_type, use_container_width=True)

# ---------------------------
#   Controls
# ---------------------------
c1, c2 = st.columns(2)
with c1:
    if st.button("🔄 Start Over (Clear Attempts)"):
        st.session_state["self_test_essays"] = []
        st.rerun()
with c2:
    st.caption("Tip: Use the sidebar to switch Part/Type and generate a new practice task.")
