import os
import sys
import json
import streamlit as st
import google.generativeai as genai
from datetime import datetime
from File_handling import read_file_content
from Connection import get_genai_connection, get_collection

st.set_page_config(page_title="Self-Test 📚", page_icon="📚")

st.title("📚 Essay Self-Test")
st.markdown(
    """
    Welcome to the **Self-Test Zone**! ✨  
    Upload your essays to practice and see how much you improve over time.  
    👉 You need to submit at least **5 essays** to unlock your progress dashboard.  
    """
)

# Initialize storage for essays in session state
if "self_test_essays" not in st.session_state:
    st.session_state["self_test_essays"] = []

# Gemini connection
get_genai_connection()
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=(
        "You are an SPM English examiner. "
        "You will analyze essays based on the official SPM marking scheme. "
        "Categories: Content, Language, Organization. "
        "Score each out of 30, then compute total (max 100). "
        "Give short feedback (strengths + weaknesses). "
        "Return JSON only."
        """
        {
            "type_of_essay": "...",
            "scores": {
                "content": ?,
                "language": ?,
                "organization": ?,
                "total": ?
            },
            "feedback": {
                "strengths": ["...", "..."],
                "weaknesses": ["...", "..."]
            }
        }
        """
    )
)

# File uploader
uploaded_file = st.file_uploader(
    "📤 Upload your essay (txt, docx, pdf, image)",
    type=["txt", "docx", "pdf", "jpg", "jpeg", "png"]
)

if uploaded_file and st.button("Analyze Essay"):
    essay_content, file_type = read_file_content(uploaded_file)

    if file_type == "unsupported":
        st.error("❌ Unsupported file type")
    else:
        with st.spinner("Analyzing essay... ✍️"):
            response = model.generate_content(essay_content)
            analysis = response.text

            # Try parse JSON
            try:
                start = analysis.find("{")
                end = analysis.rfind("}") + 1
                analysis_json = json.loads(analysis[start:end])
            except Exception:
                st.error("⚠️ Error processing essay. Please try again.")
                st.stop()

            # Store in session
            st.session_state["self_test_essays"].append({
                "essay": essay_content[:200] + "...",  # preview
                "analysis": analysis_json,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

            st.success("✅ Essay analyzed and saved!")

# Progress Tracker
num_essays = len(st.session_state["self_test_essays"])
st.progress(min(num_essays, 5) / 5)
st.write(f"📌 You have uploaded **{num_essays}/5 essays**.")

# Show essays so far
if num_essays > 0:
    st.subheader("📄 Your Essays")
    for idx, e in enumerate(st.session_state["self_test_essays"], 1):
        with st.expander(f"Essay {idx} ({e['date']})"):
            st.write("Preview:", e["essay"])
            st.json(e["analysis"])

# Unlock dashboard after 5 essays
if num_essays >= 5:
    st.subheader("📊 Your Progress Dashboard")

    import pandas as pd
    import plotly.express as px

    scores_data = []
    for i, e in enumerate(st.session_state["self_test_essays"], 1):
        scores = e["analysis"]["scores"]
        scores_data.append({
            "Essay": i,
            "Content": scores["content"],
            "Language": scores["language"],
            "Organization": scores["organization"],
            "Total": scores["total"]
        })

    df = pd.DataFrame(scores_data)

    st.write("### 📈 Score Trends")
    fig = px.line(df, x="Essay", y=["Content", "Language", "Organization", "Total"], markers=True)
    st.plotly_chart(fig)

    st.write("### 📝 Final Recommendation")
    strengths = []
    weaknesses = []
    for e in st.session_state["self_test_essays"]:
        strengths.extend(e["analysis"]["feedback"]["strengths"])
        weaknesses.extend(e["analysis"]["feedback"]["weaknesses"])

    st.markdown("**Strengths You Show Repeatedly:**")
    st.write(set(strengths))
    st.markdown("**Weaknesses to Focus On:**")
    st.write(set(weaknesses))

    st.success("🌟 Keep practicing! You’re on track to excel in SPM essays!")

# Reset button
if st.button("🔄 Start Over"):
    st.session_state["self_test_essays"] = []
    st.rerun()
