# Authentication.py
import streamlit as st
import jwt, datetime

def get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except KeyError:
        st.error(f"❌ Missing required secret: `{key}`"); st.stop()

SECRET_KEY = get_secret("JWT_SECRET_KEY")

def generate_jwt(user_id: str, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        st.error("⚠️ Session expired. Please log in again."); return None
    except jwt.InvalidTokenError:
        st.error("❌ Invalid token. Please log in again."); return None

def logout():
    st.session_state.pop("jwt_token", None)
    st.session_state.pop("user", None)
    st.success("👋 You have been logged out.")
    st.rerun()

def login_required(protected_page):
    def wrapper():
        if "jwt_token" not in st.session_state:
            st.error("🔒 You must log in to access this page.")
            if st.button("Go to Login/Register", use_container_width=True):
                st.switch_page("pages/6_Profile.py")
            st.stop()
        user_id = verify_jwt_token(st.session_state["jwt_token"])
        if user_id: protected_page()
        else: logout()
    return wrapper
