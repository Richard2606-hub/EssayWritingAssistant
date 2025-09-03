# pages/5_Performance.py
import os, sys
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Performance", page_icon="📊", layout="wide")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection
from Authentication import login_required
from Data_Visualization import display_suggestion, display_user_analysis, display_scores_over_time

st.write("# Performance 📊")

def get_past_performance(username):
    return list(get_collection("user_performance").find({"username": username}).sort("timestamp", -1))

def get_user_analysis_doc(username):
    return get_collection("user_analysis").find_one({"username": username}, sort=[('_id', -1)])

def get_self_tests(username):
    # If you saved self-tests to DB in 4_Self_Test, fetch them here
    cur = get_collection("self_test_attempts").find({"username": username}).sort("timestamp", -1)
    return [x["attempt"] for x in cur]

@login_required
def main():
    tabs = st.tabs(["Overall Performance", "Latest User Analysis", "Past Suggestions", "Self-Test History"])

    username = st.session_state["user"]["username"]
    past_performance = get_past_performance(username)
    user_analysis = get_user_analysis_doc(username)
    self_tests = get_self_tests(username)

    with tabs[0]:
        if past_performance:
            df = pd.DataFrame(past_performance)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            display_scores_over_time(df, username)
        else:
            st.info("No saved suggestions yet. Submit an essay in **Essay Suggestions**.")

    with tabs[1]:
        if user_analysis:
            st.write("### Latest User Analysis")
            display_user_analysis(user_analysis['user_info'])
        else:
            st.info("No user analysis available. Try **User Analysis** page.")

    with tabs[2]:
        if past_performance:
            # Select and render one suggestion
            label_list = [f"{i+1} - {past_performance[i]['timestamp']}" for i in range(len(past_performance))]
            selected = st.selectbox("Select a saved suggestion", label_list)
            idx = int(selected.split(" - ")[0]) - 1
            display_suggestion(past_performance[idx]["suggestions"])
        else:
            st.info("No past suggestions available.")

    with tabs[3]:
        if self_tests:
            st.write(f"Found **{len(self_tests)}** self-test attempts saved.")
            rows = []
            for i, e in enumerate(self_tests, 1):
                s = e.get("scores", {})
                rows.append({
                    "Attempt": i, "Date": e.get("date","—"), "Part": e.get("part","—"), "Type": e.get("type_of_essay","—"),
                    "Content": s.get("content"), "Organization": s.get("organization"),
                    "Language": s.get("language"), "Communicative": s.get("communicative"),
                    "Total(20)": s.get("total_out_of_20")
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No self-test attempts in the database yet.")

main()
