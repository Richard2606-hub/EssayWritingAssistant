# authentication.py
import streamlit as st
import jwt
import datetime


# ---------------------------
#   Load Secrets Safely
# ---------------------------
def get_secret(key: str) -> str:
    """Retrieve a secret safely with error handling."""
    try:
        return st.secrets[key]
    except KeyError:
        st.error(f"❌ Missing required secret: `{key}`")
        st.stop()  # Halt execution if secret is missing


SECRET_KEY = get_secret("JWT_SECRET_KEY")


# ---------------------------
#   JWT Helpers
# ---------------------------
def generate_jwt(user_id: str, username: str) -> str:
    """Generate a JWT token with 1-hour expiry."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc)
        + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_jwt_token(token: str):
    """Verify a JWT token and return the user ID if valid, else None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        st.error("⚠️ Session expired. Please log in again.")
        return None
    except jwt.InvalidTokenError:
        st.error("❌ Invalid token. Please log in again.")
        return None


def logout():
    """Clear session and force rerun."""
    st.session_state.pop("jwt_token", None)
    st.session_state.pop("user", None)
    st.success("👋 You have been logged out.")
    st.rerun()


# ---------------------------
#   Decorator for Protection
# ---------------------------
def login_required(protected_page):
    """Protect a page so only logged-in users can view it."""

    def wrapper():
        if "jwt_token" not in st.session_state:
            st.error("🔒 You must log in to access this page.")
            if st.button("Go to Login/Register", use_container_width=True):
                st.switch_page("pages/6_Profile.py")
            st.stop()

        user_id = verify_jwt_token(st.session_state["jwt_token"])
        if user_id:
            protected_page()
        else:
            logout()  # Auto-logout on invalid/expired token

    return wrapper


# ---------------------------
#   Example Public/Home Page
# ---------------------------
def home_page():
    st.title("🏠 Home")
    st.write("This page is accessible to all users.")
