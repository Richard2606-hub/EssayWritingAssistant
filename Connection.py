# Connection.py

from __future__ import annotations
import streamlit as st
import pymongo
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError
from pymongo import MongoClient
import google.generativeai as genai

# Optional OpenAI support
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# --- Load Secrets ---
def _get_secret(key: str, *, required: bool = True, default: str | None = None) -> str:
    try:
        val = st.secrets[key]
        if not isinstance(val, str) or not val.strip():
            raise KeyError
        return val.strip()
    except KeyError:
        if required:
            st.error(f"❌ Missing or empty secret: `{key}`. Check `.streamlit/secrets.toml`.")
            st.stop()
        return default or ""

MONGODB_URI = _get_secret("MONGODB_URI")
OPENAI_API_KEY = _get_secret("OPENAI_API_KEY", required=False, default="")
GEMINI_API_KEY = _get_secret("GOOGLE_API_KEY")

# --- MongoDB Setup ---
def ping_mongo(uri=MONGODB_URI, timeout=2000):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout)
        client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False

@st.cache_resource(show_spinner=False)
def init_connection() -> pymongo.MongoClient:
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=20000,
        )
        client.admin.command("ping")
        return client
    except (ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError) as e:
        st.error("❌ Could not connect to MongoDB.")
        st.caption(f"Details: {e}")
        st.stop()
    except Exception as e:
        st.error("❌ Unexpected MongoDB error.")
        st.exception(e)
        st.stop()

def get_db(db_name: str = "essay_assistant_db"):
    return init_connection()[db_name]

def get_collection(collection_name: str, db_name: str = "essay_assistant_db"):
    return get_db(db_name)[collection_name]

# --- Gemini ---
@st.cache_resource(show_spinner=False)
def get_genai_connection():
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return genai
    except Exception as e:
        st.error("❌ Failed to configure Gemini.")
        st.caption(str(e))
        st.stop()

def gemini_health_check() -> bool:
    try:
        _ = genai.GenerativeModel("gemini-1.5-flash")
        return True
    except Exception:
        return False

# --- OpenAI ---
@st.cache_resource(show_spinner=False)
def get_openai_connection() -> OpenAI | None:
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.error("❌ Failed to connect to OpenAI.")
        st.caption(str(e))
        return None

# --- Combined Report ---
def health_report() -> dict:
    return {
        "mongo_connected": ping_mongo(),
        "openai_configured": bool(OPENAI_API_KEY),
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_usable": gemini_health_check(),
    }
