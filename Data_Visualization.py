import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt


def display_suggestion(suggestions: dict):
    """Display essay suggestions, scores, and improvements."""

    # --- Essay Type ---
    st.header("📑 Essay Type")
    st.write(suggestions["essay_score"].get("type_of_essay", "N/A"))

    # --- Scores ---
    scores = suggestions["essay_score"].get("scores", {})
    if not scores:
        st.warning("⚠️ No scores available.")
        return

    scores_df = pd.DataFrame(list(scores.items()), columns=["Category", "Score"])
    scores_df["Category"] = scores_df["Category"].map(lambda x: x.replace("_", " ").title())

    # Bar chart
    fig = px.bar(
        scores_df, y="Category", x="Score", color="Score",
        labels={"Score": "Scores", "Category": "Score Categories"},
        title="Essay Evaluation Scores", text="Score"
    )
    fig.update_layout(showlegend=False, xaxis=dict(range=[0, 10]))

    st.header("📊 Scores Overview")
    st.plotly_chart(fig)

    # Data table
    scores_df["Score"] = scores_df["Score"].map("{}/10".format)
    st.dataframe(scores_df, use_container_width=True, hide_index=True)

    # --- Suggestions ---
    st.header("💡 Suggestions")
    for s in suggestions["essay_score"].get("essay_suggestion", []):
        with st.expander(f"✏️ Section {s['section']}"):
            st.subheader("Original Text")
            st.write(s["original_text"])
            st.subheader("Suggestion")
            st.write(s["suggestion"])
            st.subheader("Improved Version")
            st.write(s["improved_version"])


def display_user_analysis(user_analysis: dict):
    """Display user strengths, weaknesses, and role insights."""
    if not user_analysis:
        st.warning("⚠️ No user analysis data found.")
        return

    # Writing style
    st.header("🖋 Writing Style and Role")
    st.write(f"**Role:** {user_analysis.get('game_like_role', 'N/A')}")
    st.write(f"**Writing Style:** {user_analysis.get('writing_style', 'N/A')}")

    # Strengths
    st.header("💪 Strengths")
    for strength in user_analysis.get("strengths", []):
        st.write(f"- {strength}")

    # Weaknesses
    st.header("⚠️ Weaknesses")
    for weakness in user_analysis.get("weaknesses", []):
        st.write(f"- {weakness}")

    # Pie chart
    categories = ["Strengths", "Weaknesses"]
    values = [len(user_analysis.get("strengths", [])), len(user_analysis.get("weaknesses", []))]

    if sum(values) > 0:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(values, labels=categories, autopct="%1.1f%%", startangle=90,
               colors=["lightgreen", "salmon"])
        ax.set_title("Strengths vs. Weaknesses")
        st.pyplot(fig)


def display_scores_over_time(user_entries: pd.DataFrame, selected_username: str):
    """Plot score progress for a user over time."""
    if user_entries.empty:
        st.warning("⚠️ No past performance data available.")
        return

    scores_over_time = pd.DataFrame()
    for _, entry in user_entries.iterrows():
        scores = entry.get("suggestions", {}).get("essay_score", {}).get("scores", {})
        if not scores:
            continue
        temp_df = pd.DataFrame(list(scores.items()), columns=["Category", "Score"])
        temp_df["Timestamp"] = entry["timestamp"]
        scores_over_time = pd.concat([scores_over_time, temp_df], ignore_index=True)

    if scores_over_time.empty:
        st.warning("⚠️ No valid score data to plot.")
        return

    fig = px.line(
        scores_over_time, x="Timestamp", y="Score", color="Category",
        labels={"Score": "Scores", "Timestamp": "Date"},
        title=f"📈 Scores Over Time for {selected_username}",
        markers=True
    )
    st.plotly_chart(fig)
