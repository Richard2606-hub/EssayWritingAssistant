# connection.py
import streamlit as st
import pymongo
import datetime
from openai import OpenAI
import google.generativeai as genai

# --- Secrets ---
MONGODB_URI = st.secrets["MONGODB_URI"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GEMINIKEY = st.secrets["GOOGLE_API_KEY"]

# --- MongoDB Connection ---
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(MONGODB_URI)

def get_db():
    client = init_connection()
    return client["essay_assistant_db"]

def get_collection(collection_name: str):
    db = get_db()
    return db[collection_name]

# --- OpenAI Connection ---
@st.cache_resource
def get_openai_connection():
    return OpenAI(api_key=OPENAI_API_KEY)

# --- Gemini Connection ---
def get_genai_connection():
    if not GEMINIKEY:
        raise ValueError("Google API key is missing.")
    genai.configure(api_key=GEMINIKEY)
    return genai

# --------------------------
#   CHAT MANAGEMENT
# --------------------------
def save_chat(user_id: str, messages: list):
    """
    Save chat history for a given user.
    Uses upsert so the same user gets their chat updated instead of duplicated.
    """
    chats = get_collection("chats")
    chats.update_one(
        {"user_id": user_id},
        {"$set": {
            "messages": messages,
            "updated_at": datetime.datetime.utcnow()
        }},
        upsert=True
    )

def load_chat(user_id: str):
    """
    Load chat history for a given user.
    Returns messages list or None if no history exists.
    """
    chats = get_collection("chats")
    record = chats.find_one({"user_id": user_id})
    return record["messages"] if record else None

# --------------------------
#   ESSAY PERFORMANCE DATA
# --------------------------
def save_essay_performance(user_id: str, essay_text: str, score: int, comments: str, suggestions: list):
    """
    Save essay performance results into MongoDB.
    """
    performance_collection = get_collection("performance")
    performance_data = {
        "user_id": user_id,
        "essay_text": essay_text,
        "score": score,
        "comments": comments,
        "suggestions": suggestions,
        "timestamp": datetime.datetime.utcnow()
    }
    performance_collection.insert_one(performance_data)

def get_past_performance(user_id: str):
    """
    Retrieve past essay performance records for a user.
    """
    performance_collection = get_collection("performance")
    return list(performance_collection.find({"user_id": user_id}).sort("timestamp", -1))

# --------------------------
#   USER ANALYSIS
# --------------------------
def save_user_analysis(user_id: str, writing_style: dict):
    """
    Save or update user’s writing style analysis.
    """
    analysis_collection = get_collection("analysis")
    analysis_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "writing_style": writing_style,
                "updated_at": datetime.datetime.utcnow()
            }
        },
        upsert=True
    )

def get_user_analysis(user_id: str):
    """
    Retrieve latest user analysis.
    """
    analysis_collection = get_collection("analysis")
    return analysis_collection.find_one({"user_id": user_id})
