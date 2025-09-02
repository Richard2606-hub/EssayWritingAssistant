import os
import sys
import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- Page config ---
st.set_page_config(page_title="Essay Writing Chat", page_icon="💬")

# --- Import helpers ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_genai_connection, get_collection
from Authentication import verify_jwt_token

# --- DB Setup ---
chats_collection = get_collection("chats")

# --- Page Header ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>💬 Essay Writing Chat</h1>", unsafe_allow_html=True)
st.write("Your personal essay coach! Ask me anything about essay writing ✍️")

# --- Initialize system prompt ---
if "messages" not in st.session_state:
    system_prompt = (
        "You are an essay teacher and will only answer questions related to essay writing. "
        "You can explain essay structures, write short samples, or guide improvements. "
        "If a question is not related to essay writing, politely refuse."
    )
    if "user_info" in st.session_state:
        system_prompt += "\nStudent info:\n"
        system_prompt += "\n".join(
            f"- {k}: {v}" for k, v in st.session_state.user_info.items()
        )

    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "👋 Hello! I’m your essay coach. What would you like help with today?"}
    ]

# --- Load previous chat if user logged in ---
user_id = None
if "jwt_token" in st.session_state:
    user_id = verify_jwt_token(st.session_state["jwt_token"])
    if user_id:
        past_chat = chats_collection.find_one({"user_id": user_id})
        if past_chat:
            st.session_state.messages = past_chat["messages"]

# --- Display messages (skip system prompt) ---
for message in st.session_state.messages[1:]:
    if message["role"] == "user":
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant", avatar="📝"):
            st.markdown(message["content"])

# --- Gemini connection ---
client = get_genai_connection()
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=st.session_state.messages[0]["content"]
)

# --- Handle chat input ---
if prompt := st.chat_input("Type your essay question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="📝"):
        with st.spinner("Thinking..."):
            try:
                response = model.generate_content(
                    [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages]
                ).text
            except Exception as e:
                response = f"⚠️ Error: {e}"

            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # --- Save chat to DB if logged in ---
    if user_id:
        chats_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "messages": st.session_state.messages,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

# --- Quick action buttons ---
st.markdown("---")
st.write("🎯 Quick Help:")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📖 Sample Essay"):
        st.session_state.messages.append(
            {"role": "user", "content": "Write me a short sample essay on 'Healthy Lifestyle'."}
        )
        st.experimental_rerun()

with col2:
    if st.button("📝 Improve My Introduction"):
        st.session_state.messages.append(
            {"role": "user", "content": "How can I write a better essay introduction?"}
        )
        st.experimental_rerun()

with col3:
    if st.button("🎯 Conclusion Tips"):
        st.session_state.messages.append(
            {"role": "user", "content": "Give me some tips on writing essay conclusions."}
        )
        st.experimental_rerun()
