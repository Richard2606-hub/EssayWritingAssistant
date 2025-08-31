import os
import sys
import json
import datetime
import streamlit as st
import google.generativeai as genai
from File_handling import read_file_content
from Connection import get_collection, get_genai_connection

st.set_page_config(page_title="Self-Test", page_icon="📝")

# --- Initialize session state ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "essay_text" not in st.session_state:
    st.session_state.essay_text = ""
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

# --- Navigation helper ---
def next_step():
    st.session_state.step += 1
    st.rerun()

def restart():
    st.session_state.step = 1
    st.session_state.responses = {}
    st.session_state.essay_text = ""
    st.session_state.evaluation = None
    st.rerun()

# --- Step 1: Diagnostic Questions ---
if st.session_state.step == 1:
    st.title("📝 Self-Test: Step 1 - Diagnostic Questions")
    st.write("Answer the following questions to help us understand your writing background.")

    questions = [
        "How confident are you in essay writing? (1-10)",
        "Which part of essay writing do you struggle with the most? (grammar, ideas, structure, conclusion, etc.)",
        "Which type of essay do you find easiest? (narrative, argumentative, expository, persuasive)",
    ]

    for i, q in enumerate(questions, start=1):
        st.session_state.responses[f"Q{i}"] = st.text_input(q, key=f"q{i}")

    if st.button("➡️ Next: Essay Submission"):
        next_step()

# --- Step 2: Essay Submission ---
elif st.session_state.step == 2:
    st.title("✍️ Self-Test: Step 2 - Essay Submission")
    st.write("Submit your essay by typing, uploading a file, or uploading an image.")

    essay_text = st.text_area("Type your essay here:", height=200)

    uploaded_file = st.file_uploader("Or upload your essay file (txt, docx, pdf, image):",
                                     type=["txt", "docx", "pdf", "jpg", "jpeg", "png"])

    if uploaded_file:
        file_content, file_type = read_file_content(uploaded_file)
        if file_type != "unsupported":
            st.session_state.essay_text = file_content
        else:
            st.error("Unsupported file type.")
    else:
        st.session_state.essay_text = essay_text

    if st.session_state.essay_text.strip() and st.button("➡️ Next: Get Evaluation"):
        next_step()

# --- Step 3: Evaluation & Recommendations ---
elif st.session_state.step == 3:
    st.title("📊 Self-Test: Step 3 - Evaluation & Recommendations")

    if not st.session_state.evaluation:
        with st.spinner("Analyzing your essay..."):
            get_genai_connection()
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=(
                    "You are an SPM English essay examiner. "
                    "Evaluate the essay based on SPM criteria: content, organization, "
                    "grammar, coherence, and conclusion. "
                    "Give feedback, strengths, weaknesses, and final score (0-10). "
                    "Also suggest the most suitable essay type for the student."
                    "Output JSON format ONLY:\n"
                    "{'scores': {...}, 'strengths': [...], 'weaknesses': [...], 'recommendations': [...], 'suitable_type': '...'}"
                )
            )

            response = model.generate_content(st.session_state.essay_text).text

            # Extract JSON only
            start = response.find("{")
            end = response.rfind("}") + 1
            try:
                st.session_state.evaluation = json.loads(response[start:end])
            except:
                st.error("Failed to parse evaluation. Please retry.")
                st.stop()

    evaluation = st.session_state.evaluation
    st.subheader("📌 Results")
    st.json(evaluation)

    if st.button("➡️ Next: View Progress"):
        next_step()

# --- Step 4: Progress Dashboard ---
elif st.session_state.step == 4:
    st.title("📈 Self-Test: Step 4 - Progress Dashboard")

    st.write("Here’s your current evaluation and how you can improve:")

    evaluation = st.session_state.evaluation
    if evaluation:
        # Handle missing or different keys safely
        overall_score = None
        if "scores" in evaluation:
            overall_score = evaluation["scores"].get("overall_score") or evaluation["scores"].get("total") or None

        if overall_score is not None:
            st.metric("Overall Score", overall_score)
        else:
            st.warning("⚠️ No overall score found in the evaluation. Please check raw results below.")

        st.write("✅ Strengths:", ", ".join(evaluation.get("strengths", [])))
        st.write("⚠️ Weaknesses:", ", ".join(evaluation.get("weaknesses", [])))
        st.write("💡 Recommendations:")
        for rec in evaluation.get("recommendations", []):
            st.markdown(f"- {rec}")

        st.subheader("📜 Raw Evaluation Data (for debugging)")
        st.json(evaluation)  # <-- show full raw response for clarity

    if "user" in st.session_state:
        user = st.session_state["user"]
        collection = get_collection("self_test_results")
        collection.insert_one({
            "username": user["username"],
            "responses": st.session_state.responses,
            "essay": st.session_state.essay_text,
            "evaluation": st.session_state.evaluation,
            "timestamp": datetime.datetime.now()
        })

    st.button("🔄 Try Again", on_click=restart)
    st.button("🏠 Back to Home", on_click=lambda: st.switch_page("Home.py"))

