import streamlit as st
import jwt
import datetime

# --- Load secret safely ---
SECRET_KEY = st.secrets.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    st.error("❌ JWT secret key missing in secrets.toml")
    st.stop()

# --- JWT handling ---
def generate_jwt(user_id: str, username: str) -> str:
    """Generate a JWT token (expires in 1 hour)."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt_token(token: str):
    """Verify a JWT token and return the user ID if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        st.warning("⚠️ Your session has expired. Please log in again.")
        return None
    except jwt.InvalidTokenError:
        st.warning("⚠️ Invalid session. Please log in again.")
        return None

def logout():
    """Clear session and rerun app."""
    if "jwt_token" in st.session_state:
        del st.session_state["jwt_token"]
    st.rerun()

def login_required(protected_page):
    """Decorator to protect pages requiring login."""
    def wrapper():
        if "jwt_token" not in st.session_state:
            st.error("🔒 You must log in to view this page.")
            if st.button("Login/Register"):
                st.switch_page("pages/6_Profile.py")
            st.stop()

        user_id = verify_jwt_token(st.session_state["jwt_token"])
        if user_id:
            protected_page()
        else:
            if "jwt_token" in st.session_state:
                del st.session_state["jwt_token"]
            st.rerun()
    return wrapper

# --- Example home page (optional) ---
def home_page():
    st.title("Home")
    st.write("✅ Public page, accessible without login.")
