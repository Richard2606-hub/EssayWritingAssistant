import streamlit as st
import pymongo
from openai import OpenAI
import google.generativeai as genai

# --- Load secrets safely ---
MONGODB_URI = st.secrets.get("MONGODB_URI")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
GEMINIKEY = st.secrets.get("GOOGLE_API_KEY")

# --- MongoDB connection ---
@st.cache_resource
def init_connection():
    if not MONGODB_URI:
        st.error("❌ MongoDB URI missing in secrets.toml")
        st.stop()
    try:
        return pymongo.MongoClient(MONGODB_URI)
    except Exception as e:
        st.error(f"❌ Failed to connect to MongoDB: {e}")
        st.stop()

def get_db():
    return init_connection()["essay_assistant_db"]

def get_collection(collection_name: str):
    return get_db()[collection_name]

# --- OpenAI connection ---
@st.cache_resource
def get_openai_connection():
    if not OPENAI_API_KEY:
        st.error("❌ OpenAI API key missing in secrets.toml")
        st.stop()
    try:
        return OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.error(f"❌ Failed to initialize OpenAI client: {e}")
        st.stop()

# --- Google Gemini connection ---
def get_genai_connection():
    if not GEMINIKEY:
        st.error("❌ Google API key missing in secrets.toml")
        st.stop()
    try:
        genai.configure(api_key=GEMINIKEY)
        return genai
    except Exception as e:
        st.error(f"❌ Failed to initialize Gemini client: {e}")
        st.stop()
