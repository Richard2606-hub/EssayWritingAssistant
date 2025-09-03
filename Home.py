# Home.py
import streamlit as st

# --- MUST be first call ---
st.set_page_config(page_title="WriteSmart", page_icon="📝", layout="wide")

# --- Styling ---
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

st.markdown('<div class="hero"><h1>✍️ WriteSmart</h1>'
            '<p>Your AI writing buddy for SPM</p></div>',
            unsafe_allow_html=True)
st.write("")

st.info("Tip: If navigation buttons don’t work in your Streamlit version, use the sidebar page list.", icon="💡")

def go(path: str):
    if hasattr(st, "switch_page"):
        try:
            st.switch_page(path); return
        except Exception:
            pass
    st.warning("Direct navigation isn’t supported in this version. Use the sidebar (left).", icon="🧭")

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👩‍🎓 User Analysis", anchor=False)
        st.caption("See your strengths and focus areas (SPM lenses).")
        if st.button("Open User Analysis"):
            go("pages/1_User_Analysis.py")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📑 Essay Suggestion", anchor=False)
        st.caption("Get SPM-style scoring and concrete rewrites.")
        if st.button("Open Essay Suggestion"):
            go("pages/2_Essay_Suggestion.py")
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("💬 Essay Writing Chat", anchor=False)
        st.caption("Ask anything about SPM essay writing.")
        if st.button("Open Essay Writing Chat"):
            go("pages/3_Essay_Writing_Chat.py")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📝 Self-Test", anchor=False)
        st.caption("Practise any part/type. Unlock dashboard after 5 essays.")
        if st.button("Open Self-Test"):
            go("pages/4_Self_Test.py")
        st.markdown('</div>', unsafe_allow_html=True)

st.write("")
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Performance", anchor=False)
    st.caption("See trends across attempts and saved suggestions.")
    if st.button("Open Performance"):
        go("pages/5_Performance.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("👤 Profile / Login", anchor=False)
    if st.button("Open Profile"):
        go("pages/6_Profile.py")
    st.markdown('</div>', unsafe_allow_html=True)
