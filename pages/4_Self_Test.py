# pages/4_Self_Test.py
import os, sys, json
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from File_handling import read_file_content
from Connection import get_genai_connection, get_collection

st.set_page_config(page_title="Self-Test 📚", page_icon="📚", layout="wide")
st.title("📚 Essay Self-Test (SPM Paper 2)")
st.markdown("""
Choose the **part/type** you want to practise, submit your essay, and get **SPM-style feedback**.

- Scoring uses **4 lenses (0–5 each)** → **Total out of 20**  
- Submit at least **5 essays** to unlock your **progress dashboard**  
""")

if "self_test_essays" not in st.session_state:
    st.session_state["self_test_essays"] = []

attempts_collection = get_collection("self_test_attempts")

get_genai_connection()
MODEL_NAME = "gemini-1.5-flash"

SELF_TEST_SYSTEM = (
    "You are an SPM English Paper 2 examiner providing formative assessment.\n"
    "INPUT: one student essay (text or OCR). You will also receive the intended part/type.\n\n"
    "TASK\n"
    "- Detect/confirm part: 'Part 1' (Email) | 'Part 2' (Guided Essay) | 'Part 3' (Extended Writing).\n"
    "- Detect/confirm type_of_essay (Narrative | Descriptive | Expository | Argumentative | Article | Report | Review | Email).\n"
    "- Score FOUR lenses (0–5 each): content, organization, language, communicative. Sum to total_out_of_20 (0–20).\n"
    "- Give 2–4 strengths and 2–4 weaknesses.\n"
    "- Provide 3 short next_focus goals.\n"
    "- Output JSON ONLY.\n\n"
    "OUTPUT\n"
    "{\n"
    '  "part": "Part 1 | Part 2 | Part 3",\n'
    '  "type_of_essay": "…",\n'
    '  "scores": {"content":0-5,"organization":0-5,"language":0-5,"communicative":0-5,"total_out_of_20":0-20},\n'
    '  "feedback": {"strengths":["…"],"weaknesses":["…"]},\n'
    '  "next_focus": ["…","…","…"]\n'
    "}\n"
    "RULES: JSON only."
)
model = genai.GenerativeModel(MODEL_NAME, system_instruction=SELF_TEST_SYSTEM)

PROMPT_GEN_SYSTEM = (
    "You are an SPM Paper 2 prompt writer. Generate one realistic practice task for the requested part/type. JSON only:\n"
    "{ 'title':'…','instructions':'…','notes':['n1','n2','n3'],'word_count':'…' }\n"
    "Rules:\n"
    "- Part 1 (Email): short reply; greeting+closing; ~80 words; 2–3 notes to respond to.\n"
    "- Part 2 (Guided): exactly 3 notes; 125–150 words.\n"
    "- Part 3 (Extended): choose one of Article/Report/Review/Narrative; 200–250 words; include format cues."
)
prompt_gen = genai.GenerativeModel(MODEL_NAME, system_instruction=PROMPT_GEN_SYSTEM)

def _safe_parse_json(raw_text: str):
    start, end = raw_text.find("{"), raw_text.rfind("}") + 1
    if start == -1 or end <= 0: return None
    try: return json.loads(raw_text[start:end])
    except Exception: return None

def generate_practice_task(selected_part: str, selected_type: str):
    try:
        raw = prompt_gen.generate_content(f"Part: {selected_part}; Type: {selected_type}. Generate one practice task.").text
        return _safe_parse_json(raw)
    except Exception:
        return None

with st.sidebar:
    st.header("🎯 Choose Practice")
    part = st.radio(
        "Select Paper 2 Part",
        options=["Part 1 (Email)", "Part 2 (Guided Essay)", "Part 3 (Extended Writing)"],
        index=0
    )
    subtype = "Email" if "Part 1" in part else ("Guided Essay" if "Part 2" in part else st.selectbox(
        "Choose a type for Part 3", ["Article","Report","Review","Narrative"], index=0
    ))
    st.markdown("---")
    if st.button("🎲 Generate a Practice Task"):
        task = generate_practice_task("Part 1" if "Part 1" in part else "Part 2" if "Part 2" in part else "Part 3", subtype)
        if task:
            st.session_state["last_generated_task"] = task
            st.success("Practice task generated below.")
        else:
            st.error("Could not generate a task. Please try again.")

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

st.markdown("### ✍️ Submit Your Essay")
tabs = st.tabs(["Type Text", "Upload File", "Upload Image"])
essay_text = None

with tabs[0]:
    essay_text = st.text_area("Type or paste your essay here", height=220, placeholder="Write your essay here…")

from File_handling import read_file_content
with tabs[1]:
    file_u = st.file_uploader("Upload a text/docx/pdf file", type=["txt","doc","docx","pdf"], key="file_upl")
    if file_u is not None:
        content, ftype = read_file_content(file_u)
        if ftype == "unsupported":
            st.error("❌ Unsupported file type.")
        elif isinstance(content, str):
            st.success(f"Loaded {file_u.name}")
            essay_text = content

with tabs[2]:
    img_u = st.file_uploader("Upload an image (jpg/png) of your essay (OCR)", type=["jpg","jpeg","png"], key="img_upl")
    if img_u is not None:
        content, itype = read_file_content(img_u)
        essay_text = content  # PIL.Image – model can handle multimodal

analyze_clicked = st.button("🔎 Analyze Essay", type="primary", use_container_width=True)

if analyze_clicked:
    if essay_text is None or (isinstance(essay_text, str) and not essay_text.strip()):
        st.error("Please provide your essay before analyzing."); st.stop()

    chosen_part = "Part 1" if "Part 1" in part else "Part 2" if "Part 2" in part else "Part 3"
    chosen_type = subtype

    with st.spinner("Analyzing essay..."):
        try:
            payload = []
            if isinstance(essay_text, str):
                payload.append(f"Intended part: {chosen_part}\nIntended type: {chosen_type}\n\nESSAY:\n{essay_text}")
            else:
                payload.append(f"Intended part: {chosen_part}\nIntended type: {chosen_type}\n\nESSAY (image attached)")
                payload.append(essay_text)
            raw = model.generate_content(payload).text
        except Exception as e:
            st.error(f"Model error: {e}"); st.stop()

        analysis_json = _safe_parse_json(raw)
        if not analysis_json:
            st.error("⚠️ Could not parse AI response."); st.stop()

        scores = analysis_json.get("scores", analysis_json.get("analysis", {}).get("scores", {}))
        if not scores:
            scores = {}
            analysis_json["scores"] = scores

        need = ["content","organization","language","communicative"]
        if "total_out_of_20" not in scores and all(k in scores for k in need):
            try:
                scores["total_out_of_20"] = int(
                    float(scores["content"]) + float(scores["organization"]) +
                    float(scores["language"]) + float(scores["communicative"])
                )
            except Exception:
                pass

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

        if "user" in st.session_state:
            try:
                attempts_collection.insert_one({"username": st.session_state["user"]["username"], "attempt": record, "timestamp": datetime.utcnow()})
            except Exception:
                pass

        st.success("✅ Essay analyzed and saved below!")

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
                for x in fb.get("strengths", []): st.write(f"- {x}")
                st.write("**Weaknesses:**")
                for x in fb.get("weaknesses", []): st.write(f"- {x}")
            nf = e.get("next_focus", [])
            if nf:
                st.write("**Next Focus:**")
                for x in nf: st.write(f"- {x}")

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

    st.write("### 📈 Lens Trends (0–5 each) & Total(20)")
    fig = px.line(df, x="Attempt", y=["Content","Organization","Language","Communicative","Total(20)"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.write("### 🧠 Average Scores by Essay Type")
    by_type = df.groupby("Type")[["Content","Organization","Language","Communicative","Total(20)"]].mean().reset_index()
    st.dataframe(by_type, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    if st.button("🔄 Start Over (Clear Attempts)"):
        st.session_state["self_test_essays"] = []; st.rerun()
with c2:
    st.caption("Tip: Use the sidebar to switch Part/Type and generate a new practice task.")
