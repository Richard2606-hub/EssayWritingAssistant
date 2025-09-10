# Connection.py
"""
Centralised connections for MongoDB, OpenAI, and Google Generative AI (Gemini).

- Reads required secrets from Streamlit's st.secrets
  * MONGODB_URI
  * OPENAI_API_KEY
  * GOOGLE_API_KEY
- Provides cached clients and simple health checks.
"""

from __future__ import annotations

import os
import traceback
import streamlit as st
import pymongo
from pymongo.errors import ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError, MongoClient

# Optional: only import OpenAI if you actually call it
try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

import google.generativeai as genai


# ---------------------------
# Secrets & helpers
# ---------------------------

def _get_secret(key: str, *, required: bool = True, default: str | None = None) -> str:
    """
    Read a secret from st.secrets with a clear error message.
    """
    try:
        val = st.secrets[key]
        if not isinstance(val, str) or not val.strip():
            raise KeyError
        return val.strip()
    except KeyError:
        if required:
            st.error(f"❌ Missing or empty secret: `{key}`. "
                     f"Add it to your `.streamlit/secrets.toml`.")
            st.stop()
        return default or ""


# Required secrets (fail fast with useful message)
MONGODB_URI: str = _get_secret("MONGODB_URI")
OPENAI_API_KEY: str = _get_secret("OPENAI_API_KEY", required=False, default="")
GEMINI_API_KEY: str = _get_secret("GOOGLE_API_KEY")


# ---------------------------
# MongoDB
# ---------------------------

@st.cache_resource(show_spinner=False)
def init_connection() -> pymongo.MongoClient:
    """
    Initialise a cached MongoDB client.
    """
    try:
        client = pymongo.MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,  # fail fast
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
        # Ping once to ensure connectivity
        client.admin.command("ping")
        return client
    except (ConnectionFailure, ConfigurationError, ServerSelectionTimeoutError) as e:
        st.error("❌ Could not connect to MongoDB. "
                 "Check your `MONGODB_URI` and that the server is running.")
        st.caption(f"Details: {e}")
        st.stop()
    except Exception as e:  # pragma: no cover
        st.error("❌ Unexpected MongoDB error.")
        st.exception(e)
        st.stop()


def get_db(db_name: str = "essay_assistant_db") -> pymongo.database.Database:
    return init_connection()[db_name]


def get_collection(collection_name: str, db_name: str = "essay_assistant_db") -> pymongo.collection.Collection:
    return get_db(db_name)[collection_name]


def ping_mongo() -> bool:
    """
    Return True if MongoDB responds to ping.
    """
    try:
        init_connection().admin.command("ping")
        return True
    except Exception:
        return False


# ---------------------------
# OpenAI (optional)
# ---------------------------

@st.cache_resource(show_spinner=False)
def get_openai_connection() -> OpenAI | None:
    """
    Returns a cached OpenAI client or None if no API key is configured.
    """
    if not OPENAI_API_KEY:
        # Not fatal—some pages use Gemini only.
        st.warning("🔐 OPENAI_API_KEY not set. Skipping OpenAI client.")
        return None
    if OpenAI is None:
        st.warning("⚠️ `openai` package not available. Skipping OpenAI client.")
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        return client
    except Exception as e:  # pragma: no cover
        st.error("❌ Failed to initialise OpenAI client.")
        st.caption(str(e))
        return None


# ---------------------------
# Google Generative AI (Gemini)
# ---------------------------

@st.cache_resource(show_spinner=False)
def get_genai_connection():
    """
    Configure and return the google.generativeai module (singleton style).
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return genai
    except Exception as e:  # pragma: no cover
        st.error("❌ Failed to configure Google Generative AI (Gemini).")
        st.caption(str(e))
        st.stop()


def gemini_health_check() -> bool:
    """
    Lightweight check: attempts to create a trivial model instance.
    """
    try:
        _ = genai.GenerativeModel("gemini-1.5-flash")
        return True
    except Exception:
        return False


# ---------------------------
# Optional overall health check
# ---------------------------

def health_report() -> dict:
    """
    Return a quick health snapshot useful for a debug panel.
    """
    report = {
        "mongo_connected": ping_mongo(),
        "openai_configured": bool(OPENAI_API_KEY),
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_usable": gemini_health_check(),
    }
    return report
