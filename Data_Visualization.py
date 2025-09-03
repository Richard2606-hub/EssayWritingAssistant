# Data_Visualization.py
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

def display_suggestion(suggestions):
    """Render suggestions in your historical format, but supports 4 lenses + total(20)."""
    st.header("Essay Type")
    st.write(suggestions["essay_score"]["type_of_essay"])

    scores = suggestions['essay_score']['scores']
    # Build lenses
    rows = []
    lens_map = [
        ("content","Content"),
        ("organization","Organization"),
        ("language","Language"),
        ("communicative","Communicative"),
    ]
    for key, label in lens_map:
        if key in scores:
            rows.append({"Category": label, "Score": float(scores[key])})

    df = pd.DataFrame(rows)
    fig = px.bar(df, y='Category', x='Score', color='Score',
                 labels={'Score': 'Score (0–5)', 'Category': 'Lenses'},
                 title='SPM Lenses (0–5 each)', text='Score')
    fig.update_layout(showlegend=False, xaxis=dict(range=[0,5]))
    st.header("Scores")
    st.plotly_chart(fig, use_container_width=True)

    if "total_out_of_20" in scores:
        st.markdown(f"**Total (out of 20):** `{int(scores['total_out_of_20'])}`")

    df_table = df.copy()
    if not df_table.empty:
        df_table["Score"] = df_table["Score"].map(lambda v: f"{v:.1f}/5")
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    st.header("Suggestions")
    for s in suggestions["essay_score"]["essay_suggestion"]:
        with st.expander(f"Section {s.get('section','-')}"):
            st.subheader("Original Text"); st.write(s.get("original_text","—"))
            st.subheader("Suggestion");    st.write(s.get("suggestion","—"))
            st.subheader("Improved Version"); st.write(s.get("improved_version","—"))

def display_user_analysis(user_analysis):
    st.header("Writing Style and Role")
    st.write(f"**Role:** {user_analysis.get('game_like_role','—')}")
    st.write(f"**Writing Style:** {user_analysis.get('writing_style','—')}")

    indic = user_analysis.get("indicative_scores")
    if indic and all(k in indic for k in ["content","organization","language","communicative"]):
        rows = [
            {"Category":"Content","Score":indic["content"]},
            {"Category":"Organization","Score":indic["organization"]},
            {"Category":"Language","Score":indic["language"]},
            {"Category":"Communicative","Score":indic["communicative"]},
        ]
        df = pd.DataFrame(rows)
        fig = px.bar(df, y="Category", x="Score", color="Score",
                     labels={"Score":"Score (0–5)","Category":"Lenses"},
                     title="Indicative SPM Lenses", text="Score")
        fig.update_layout(showlegend=False, xaxis=dict(range=[0,5]))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Total (20): {indic.get('total_out_of_20','—')}")

    st.header("Strengths")
    for s in user_analysis.get("strengths", []): st.write(f"- {s}")

    st.header("Weaknesses")
    for w in user_analysis.get("weaknesses", []): st.write(f"- {w}")

def display_scores_over_time(df: pd.DataFrame, selected_username: str):
    """df rows contain {'suggestions': {essay_score:{scores: {…}}}, 'timestamp': …}"""
    scores_over_time = pd.DataFrame()
    for _, entry in df.iterrows():
        # support both old and new shapes
        s = (entry.get('suggestions', {})
                .get('essay_score', {})
                .get('scores', {}))
        ts = entry['timestamp']
        for key, label in [("content","Content"),("organization","Organization"),
                           ("language","Language"),("communicative","Communicative")]:
            if key in s:
                scores_over_time = pd.concat([scores_over_time, pd.DataFrame([{
                    "Timestamp": ts, "Category": label, "Score": s[key]
                }])], ignore_index=True)

        if "total_out_of_20" in s:
            scores_over_time = pd.concat([scores_over_time, pd.DataFrame([{
                "Timestamp": ts, "Category": "Total(20)", "Score": s["total_out_of_20"]
            }])], ignore_index=True)

    if scores_over_time.empty:
        st.info("No scores to plot yet."); return

    fig = px.line(scores_over_time, x='Timestamp', y='Score', color='Category',
                  labels={'Score':'Score', 'Timestamp':'Date'},
                  title=f'Scores Over Time for {selected_username}', markers=True)
    st.plotly_chart(fig, use_container_width=True)
