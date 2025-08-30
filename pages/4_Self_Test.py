import os
import sys
import json
import streamlit as st
import plotly.express as px
from datetime import datetime
import google.generativeai as genai

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection, get_genai_connection
from Authentication import login_required

st.set_page_config(page_title="SPM Self-Test", page_icon="📝", layout="wide")

# ------------------- Main -------------------
def main():
    st.title("📝 SPM Essay Self-Test")
    st.write("Welcome! This test will help you discover your strengths, weaknesses, "
             "and the best essay type for you in the SPM exam. 🚀")

    # Track progress
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0

    # ---------------- Step 1: Questionnaire ----------------
    if st.session_state.step == 1:
        st.subheader("📋 Step 1: Tell us about yourself")
        questions = [
            "What is your current level of study? (e.g. Form 4, Form 5)",
            "How would you rate your English writing skills? (1-10)",
            "Which essay type do you usually prefer? (narrative, argumentative, descriptive, factual, reflective, directed writing)",
            "Do you have specific areas where you struggle? (grammar, ideas, structure, etc.)",
            "How often do you practice essay writing? (daily, weekly, rarely)"
        ]

        q_index = len(st.session_state.responses)
        if q_index < len(questions):
            response = st.text_input(questions[q_index], key=f"q{q_index}")
            if st.button("Next"):
                st.session_state.responses[questions[q_index]] = response
                st.rerun()
        else:
            st.success("✅ Questionnaire complete!")
            st.session_state.step = 2
            st.rerun()

    # ---------------- Step 2: Mini Quiz ----------------
    elif st.session_state.step == 2:
        st.subheader("🎯 Step 2: Quick Grammar & Vocabulary Quiz")

        quiz = [
            {
                "q": "Choose the correct sentence:",
                "options": ["He go to school everyday.", "He goes to school every day."],
                "answer": 1,
            },
            {
                "q": "What is the synonym of 'happy'?",
                "options": ["Sad", "Joyful", "Angry"],
                "answer": 1,
            },
        ]

        q_index = st.session_state.quiz_score + len(st.session_state.responses)
        if "quiz_index" not in st.session_state:
            st.session_state.quiz_index = 0

        if st.session_state.quiz_index < len(quiz):
            q = quiz[st.session_state.quiz_index]
            st.write(q["q"])
            choice = st.radio("Options:", q["options"], key=f"quiz{st.session_state.quiz_index}")
            if st.button("Submit Answer"):
                if q["options"].index(choice) == q["answer"]:
                    st.session_state.quiz_score += 1
                    st.success("Correct! 🎉")
                else:
                    st.error("Oops! Try to improve this area.")
                st.session_state.quiz_index += 1
                st.rerun()
        else:
            st.info(f"Quiz complete! Your score: {st.session_state.quiz_score}/{len(quiz)}")
            st.session_state.step = 3
            st.rerun()

    # ---------------- Step 3: AI Analysis ----------------
    elif st.session_state.step == 3:
        st.subheader("🤖 Step 3: Personalized Analysis & SPM Focus")

        get_genai_connection()
        system_prompt = (
            "You are an SPM English teacher. Analyze the student's responses and quiz. "
            "Give: strengths, weaknesses, learning style, and assign a fun role. "
            "Then, recommend ONE SPM essay type (Narrative, Descriptive, Argumentative, Reflective, Factual, Directed Writing) "
            "that best fits the student’s strengths. "
            "Also, give a simple writing challenge for that essay type (max 200 words). "
            "Keep feedback student-friendly and motivating."
        )

        profile_data = json.dumps({
            "responses": st.session_state.responses,
            "quiz_score": st.session_state.quiz_score
        }, indent=2)

        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)

        with st.spinner("Analyzing your responses..."):
            response = model.generate_content(profile_data)
            result = response.text

        st.success("🎉 Here’s your personalized analysis & recommendation!")
        st.markdown(result)

        st.session_state.analysis = result
        st.session_state.step = 4

    # ---------------- Step 4: Essay Practice ----------------
    elif st.session_state.step == 4:
        st.subheader("✍️ Step 4: Your Practice Zone")
        st.write("Now try writing a short essay based on your recommended essay type!")

        user_essay = st.text_area("Write your essay here...", height=250)

        if st.button("Submit Essay for Feedback"):
            with st.spinner("Evaluating your essay..."):
                practice_prompt = (
                    f"Evaluate this student essay based on SPM marking scheme.\n"
                    f"Essay: {user_essay}\n"
                    f"Provide: scores (Content, Language, Organization), strengths, weaknesses, "
                    f"and 3 improvement tips. Keep it under 200 words."
                )
                practice_model = genai.GenerativeModel("gemini-1.5-flash")
                practice_feedback = practice_model.generate_content(practice_prompt).text

            st.success("✅ Feedback Received!")
            st.markdown(practice_feedback)

            # Save to DB if user logged in
            if "user" in st.session_state:
                collection = get_collection("self_test_practice")
                collection.insert_one({
                    "username": st.session_state["user"]["username"],
                    "essay": user_essay,
                    "feedback": practice_feedback,
                    "timestamp": datetime.now()
                })

            st.session_state.last_feedback = practice_feedback
            st.session_state.step = 5

    # ---------------- Step 5: Progress Dashboard ----------------
    elif st.session_state.step == 5:
        st.subheader("📊 Step 5: Your Progress Dashboard")

        # Simulated progress data
        progress = {
            "Narrative": 3,
            "Argumentative": 1,
            "Descriptive": 2,
            "Reflective": 0,
            "Factual": 1,
            "Directed Writing": 0
        }
        df = json.loads(json.dumps(progress))
        fig = px.bar(x=list(df.keys()), y=list(df.values()), labels={"x": "Essay Type", "y": "Attempts"},
                     title="Essay Type Attempts")

        st.plotly_chart(fig)

        st.info("🎯 Tip: Focus more on essay types with fewer attempts!")

        if st.button("Restart Self-Test"):
            st.session_state.step = 1
            st.session_state.responses = {}
            st.session_state.quiz_score = 0
            st.rerun()

# ------------------- Run -------------------
if __name__ == "__main__":
    main()
