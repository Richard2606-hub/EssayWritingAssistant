# pages/4_Self_Test.py
import os, sys, json
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

st.set_page_config(page_title="Self-Test 📚", page_icon="📚", layout="wide")

# --- Local imports ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_genai_connection, get_collection
from File_handling import read_file_content

st.title("📚 Essay Self-Test (SPM Paper 2)")
st.markdown(
    """
    Practice with **SPM-style scoring (4 lenses, 0–5 each → total /20)**, short feedback, and next steps.  
    👉 Upload **at least 5 attempts** to unlock your progress dashboard.
    """
)

# State
if "self_test_essays" not in st.session_state:
    st.session_state["self_test_essays"] = []

# --- Practice selector ---
with st.sidebar:
    st.header("🎛️ Practice Setup")
    part = st.selectbox("Choose Part", ["Part 1 (Email)", "Part 2 (Guided Essay)", "Part 3 (Extended Writing)"])
    if part == "Part 3 (Extended Writing)":
        subtype = st.selectbox("Type (Part 3)", ["Article", "Report", "Review", "Narrative"])
    else:
        subtype = st.selectbox("Type", ["Email"] if "Part 1" in part else ["Descriptive", "Expository", "Argumentative", "Narrative"])

    st.caption("Tip: You can paste text, upload a file, or upload an image of your essay.")

# --- AI Setup ---
get_genai_connection()

SYSTEM_PROMPT = (
    "You are an **SPM English Paper 2 examiner**.\n"
    "You will receive ONE student essay (text/docx/pdf/image OCR) and the intended task label (Part/Type). "
    "Return **JSON ONLY** (no code fences). Keep feedback concise and exam-focused.\n\n"

    "RUBRIC (0–5 per lens; integers only)\n"
    "CONTENT\n"
    "  0 Off-task/irrelevant | 1 Barely addresses; very thin | 2 Partly relevant; ≥1 point missing/misinterpreted; thin; generic examples | "
    "  3 Generally addresses; some development; minor omissions | 4 All points present; mostly developed; minor lapses | 5 Fully relevant; well-developed with apt examples\n"
    "ORGANIZATION\n"
    "  0 No structure | 1 Minimal paragraphing; poor flow | 2 Weak structure; abrupt jumps; limited devices; sequence sometimes confusing | "
    "  3 Logical sequence; basic cohesion; some weak links | 4 Clear structure; mostly smooth transitions; occasional slips | 5 Clear intro/body/end; smooth, cohesive\n"
    "LANGUAGE\n"
    "  0 Very frequent errors; hard to understand | 1 Many basic errors; meaning often unclear | 2 Errors sometimes impede meaning; basic/repetitive; limited vocab | "
    "  3 Mostly accurate; some slips; adequate range | 4 Generally accurate; minor slips; some variety; apt vocab | 5 Accurate, varied, effective word choice; appropriate tone\n"
    "COMMUNICATIVE\n"
    "  0 Wrong/ignored task | 1 Major format/tone issues; notes not covered | 2 Partly achieved; several notes missing/wrong; tone off; key format missing | "
    "  3 Mostly achieved; basic format present; minor omissions | 4 Achieved; all notes addressed (one may be shallow); appropriate tone; format mostly correct | 5 Fully achieved; all requirements met; strong genre conventions\n\n"

    "OUTPUT JSON SCHEMA (STRICT)\n"
    "{\n"
    '  "intended": { "part": "Part 1|Part 2|Part 3", "type": "Email|Article|Report|Review|Narrative|Descriptive|Expository|Argumentative" },\n'
    '  "detected": { "part": "Part 1|Part 2|Part 3|Mixed", "type": "Email|Article|Report|Review|Narrative|Descriptive|Expository|Argumentative|Mixed" },\n'
    '  "scores": { "content": 0-5, "organization": 0-5, "language": 0-5, "communicative": 0-5, "total_out_of_20": 0-20 },\n'
    '  "feedback": { "strengths": ["..."], "weaknesses": ["..."] },\n'
    '  "next_focus": ["three concrete actions"],\n'
    '  "recommended_part3_choices": ["two most suitable if this were Part 3, e.g., Narrative, Article"]\n'
    "}\n\n"
    "RULES\n"
    "- JSON ONLY. Keep bullets short. Choose nearest integer for each lens."
)

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)

# --- Input area ---
st.subheader("✍️ Submit Your Essay")
essay_text = st.text_area("Paste your essay here (optional)", height=180, placeholder="Paste your essay text...")
uploaded_file = st.file_uploader("Or upload a file (txt, docx, pdf, or image)", type=["txt", "doc", "docx", "pdf", "jpg", "jpeg", "png"])

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

def _label_to_intended(part_label: str, type_label: str):
    p = "Part 1" if part_label.startswith("Part 1") else "Part 2" if part_label.startswith("Part 2") else "Part 3"
    return {"part": p, "type": type_label}

if st.button("Analyze Essay"):
    # collect content
    content = None
    if essay_text and essay_text.strip():
        content = essay_text.strip()
    elif uploaded_file:
        read, ftype = read_file_content(uploaded_file)
        if ftype == "unsupported":
            st.error("❌ Unsupported file")
            st.stop()
        content = read
    else:
        st.warning("Please paste text or upload a file.")
        st.stop()

    intended = _label_to_intended(part, subtype)

    with st.spinner("Scoring your essay..."):
        try:
            raw = model.generate_content([json.dumps({"intended": intended}), content]).text
        except Exception as e:
            st.error(f"Model error: {e}")
            st.stop()

    data = _safe_parse_json(raw)
    if not data:
        st.error("⚠️ Could not parse AI response. Please try again.")
        st.stop()

    # normalize
    data.setdefault("intended", intended)
    data.setdefault("detected", {"part": "Mixed", "type": "Mixed"})
    data.setdefault("scores", {})
    data["scores"] = _fix_scores(data["scores"])
    data.setdefault("feedback", {"strengths": [], "weaknesses": []})
    data.setdefault("next_focus", [])
    data.setdefault("recommended_part3_choices", [])

    # store attempt
    st.session_state["self_test_essays"].append({
        "intended": data["intended"],
        "detected": data["detected"],
        "analysis": data,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    # optional DB save
    if "user" in st.session_state:
        get_collection("user_performance").insert_one({
            "username": st.session_state["user"]["username"],
            "self_test": data,
            "timestamp": datetime.now()
        })

    st.success("✅ Essay analyzed and saved!")

# --- Progress & History ---
num_essays = len(st.session_state["self_test_essays"])
st.progress(min(num_essays, 5) / 5)
st.caption(f"Uploaded attempts: **{num_essays}/5**")

if num_essays:
    st.subheader("📄 Your Attempts")
    for i, item in enumerate(st.session_state["self_test_essays"], 1):
        a = item["analysis"]
        scores = a.get("scores", {})
        with st.expander(f"Attempt {i} — {item['date']}"):
            st.markdown(
                f"- **Intended:** {item['intended']['part']} / {item['intended']['type']}\n"
                f"- **Detected:** {a.get('detected',{}).get('part','—')} / {a.get('detected',{}).get('type','—')}\n"
                f"- **Scores:** Content {scores.get('content','—')}, Org {scores.get('organization','—')}, "
                f"Lang {scores.get('language','—')}, Comm {scores.get('communicative','—')} → **Total {scores.get('total_out_of_20','—')}/20**"
            )
            fb = a.get("feedback", {})
            if fb.get("strengths"):
                st.write("**Strengths:**")
                for s in fb["strengths"]:
                    st.write(f"- {s}")
            if fb.get("weaknesses"):
                st.write("**Weaknesses:**")
                for w in fb["weaknesses"]:
                    st.write(f"- {w}")
            if a.get("next_focus"):
                st.write("**Next Focus:**")
                for tip in a["next_focus"]:
                    st.write(f"- {tip}")
            if a.get("recommended_part3_choices"):
                st.write("**Suggested Part 3 choices (based on your writing):**")
                st.write(", ".join(a["recommended_part3_choices"]))

# --- Dashboard after 5 ---
if num_essays >= 5:
    st.subheader("📊 Progress Dashboard")
    rows = []
    for idx, item in enumerate(st.session_state["self_test_essays"], 1):
        s = item["analysis"].get("scores", {})
        rows.append({
            "Attempt": idx,
            "Content": s.get("content", None),
            "Organization": s.get("organization", None),
            "Language": s.get("language", None),
            "Communicative": s.get("communicative", None),
            "Total": s.get("total_out_of_20", None),
            "Type": f"{item['intended']['part']} / {item['intended']['type']}"
        })
    df = pd.DataFrame(rows)

    st.write("### 📈 Score Trends")
    fig = px.line(df, x="Attempt", y=["Content","Organization","Language","Communicative","Total"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.write("### 📌 Averages by Intended Type")
    avg = df.groupby("Type")[["Content","Organization","Language","Communicative","Total"]].mean().round(2).reset_index()
    st.dataframe(avg, use_container_width=True)

    st.success("🌟 Keep practising — your consistency builds exam confidence!")


c1, c2 = st.columns(2)
with c1:
    if st.button("🔄 Start Over (Clear Attempts)"):
        st.session_state["self_test_essays"] = []; st.rerun()
with c2:
    st.caption("Tip: Use the sidebar to switch Part/Type and generate a new practice task.")
