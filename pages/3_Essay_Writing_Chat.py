# pages/3_Essay_Writing_Chat.py

import os, sys
import streamlit as st
import google.generativeai as genai
from datetime import datetime

st.set_page_config(page_title="Essay Writing Chat", page_icon="💬")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Connection import get_genai_connection, get_collection, ping_mongo
from Authentication import verify_jwt_token

# --- Title and Setup ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>💬 Essay Writing Chat</h1>", unsafe_allow_html=True)
st.write("Your personal essay coach! Ask me anything about SPM essay writing ✍️")

# --- MongoDB Health Check ---
if not ping_mongo():
    st.error("🚫 MongoDB is not reachable. Make sure MongoDB is running at `localhost:27017`.")
else:
    st.success("✅ MongoDB connected successfully.")

# --- Session Setup ---
if "messages" not in st.session_state:
    system_prompt = (
        "You are an SPM Paper 2 essay coach for secondary school students.\n"
        "SCOPE: ONLY essay-writing (planning, structure, linking, tone, grammar, model openings).\n"
        "If off-topic, politely refuse and suggest an essay-related angle.\n"
        "When asked for a sample, give a brief model paragraph or outline.\n"
        "Align guidance to SPM task types:\n"
        "- Part 1: informal email (~80 words)\n"
        "- Part 2: guided essay (125–150 words using ALL given notes)\n"
        "- Part 3: choose ONE of Article | Story | Report | Review."
    )
    if "user_info" in st.session_state:
        system_prompt += "\nStudent info:\n" + "\n".join(f"- {k}: {v}" for k, v in st.session_state.user_info.items())
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "👋 Hello! I’m your essay coach. How can I help?"}
    ]

# --- Load Chat History ---
user_id = None
chats_collection = None

if "jwt_token" in st.session_state:
    user_id = verify_jwt_token(st.session_state["jwt_token"])
    if user_id:
        try:
            chats_collection = get_collection("chats")
            past_chat = chats_collection.find_one({"user_id": user_id})
            if past_chat:
                st.session_state.messages = past_chat["messages"]
        except Exception as e:
            st.warning(f"⚠️ Could not load chat history: {e}")

# --- Display Messages ---
for m in st.session_state.messages[1:]:
    with st.chat_message("user" if m["role"] == "user" else "assistant",
                         avatar="🧑‍🎓" if m["role"] == "user" else "📝"):
        st.markdown(m["content"])

# --- Gemini Model ---
get_genai_connection()
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction=st.session_state.messages[0]["content"]
)

# --- Chat Input ---
if prompt := st.chat_input("Type your essay question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="📝"):
        with st.spinner("Thinking..."):
            try:
                reply = model.generate_content(
                    [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages]
                ).text
            except Exception as e:
                reply = f"⚠️ Error: {e}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    if user_id and chats_collection:
        try:
            chats_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "messages": st.session_state.messages,
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
        except Exception as e:
            st.warning(f"⚠️ Failed to save chat: {e}")

# --- Quick Help ---
st.markdown("---")
st.write("🎯 Quick Help:")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📖 Sample Essay"):
        st.session_state.messages.append(
            {"role": "user", "content": "Write a short sample opening for a Part 2 guided essay on healthy lifestyle."}
        )
        st.rerun()

with col2:
    if st.button("📝 Improve My Introduction"):
        st.session_state.messages.append(
            {"role": "user", "content": "How can I write a stronger thesis/intro for a guided essay?"}
        )
        st.rerun()

with col3:
    if st.button("🎯 Conclusion Tips"):
        st.session_state.messages.append(
            {"role": "user", "content": "Give 3 tips for writing a good conclusion for Part 3 Article."}
        )
        st.rerun()
