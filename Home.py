# Home.py
import streamlit as st

# --- MUST be first Streamlit call ---
st.set_page_config(page_title="WriteSmart", page_icon="📝", layout="wide")

# --- Light, stable styling (no fragile selectors) ---
st.markdown("""
    <style>
      .hero { text-align:center; margin-top:0.5rem; }
      .hero h1 { font-size: 2.2rem; margin-bottom:0.25rem; color:#2E86C1; }
      .hero p { font-size: 1.05rem; color:#117864; }
      .card { background:#F8F9F9; padding:1rem; border-radius:14px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
      .stButton>button { width:100%; height:56px; border-radius:12px; font-size:1rem;
                         font-weight:600; background:#2E86C1; color:white; border:none; }
      .stButton>button:hover { background:#1B4F72; }
    </style>
""", unsafe_allow_html=True)

# --- Header / hero ---
st.markdown('<div class="hero"><h1>✍️ WriteSmart</h1>'
            '<p>Your AI writing buddy for SPM • MUET • IELTS</p></div>',
            unsafe_allow_html=True)
st.write("")

st.info("Tip: If navigation buttons don’t work on your Streamlit version, use the sidebar page list.", icon="💡")

# Safe helper for navigation across Streamlit versions
def go(path: str):
    if hasattr(st, "switch_page"):
        try:
            st.switch_page(path)
            return
        except Exception:
            pass
    st.warning("Direct navigation isn’t supported in this version. Please open the page from the left sidebar.", icon="🧭")

# --- Feature grid ---
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👩‍🎓 User Analysis", anchor=False)
        st.caption("See your strengths and focus areas at a glance.")
        if st.button("Open User Analysis"):
            go("pages/1_User_Analysis.py")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📑 Essay Suggestion", anchor=False)
        st.caption("Get exam-style prompts and topic ideas.")
        if st.button("Open Essay Suggestion"):
            go("pages/2_Essay_Suggestion.py")
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("💬 Essay Writing Chat", anchor=False)
        st.caption("Write, ask questions, and get instant AI tips.")
        if st.button("Open Essay Writing Chat"):
            go("pages/3_Essay_Writing_Chat.py")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📝 Self Analysis", anchor=False)
        st.caption("Quick checks on grammar, coherence, and vocab.")
        if st.button("Open Self Analysis"):
            go("pages/4_Self_Test.py")
        st.markdown('</div>', unsafe_allow_html=True)
