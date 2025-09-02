# profile.py
import os
import sys
import bcrypt
import streamlit as st
from bson import ObjectId

# Local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection
from Authentication import generate_jwt, verify_jwt_token, logout

# --- MongoDB connection ---
users_collection = get_collection("users")


# ---------------------------
#   Authentication UI
# ---------------------------
def login_page():
    """Render Register/Login tabs."""
    tab1, tab2 = st.tabs(["🆕 Register", "🔑 Login"])

    with tab1:
        register_tab()
    with tab2:
        login_tab()


def register_tab():
    st.subheader("Create an Account")
    username = st.text_input("Username", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Register", use_container_width=True):
        register_user(username, email, password)


def login_tab():
    st.subheader("Login to Your Account")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", use_container_width=True):
        login_user(username, password)


# ---------------------------
#   Authentication Logic
# ---------------------------
def register_user(username: str, email: str, password: str):
    """Register a new user if credentials are valid."""
    if not username or not email or not password:
        st.error("⚠️ Please fill in all the fields.")
        return

    if users_collection.find_one({"username": username}):
        st.error("⚠️ Username already exists. Please choose another.")
        return

    if users_collection.find_one({"email": email}):
        st.error("⚠️ Email already registered. Please use another.")
        return

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    users_collection.insert_one(
        {
            "username": username,
            "email": email,
            "password": hashed_password,
            "picture": "https://www.shutterstock.com/image-vector/blank-avatar-photo-place-holder-600nw-1114445501.jpg",
        }
    )
    st.success("✅ Registration successful! You can now log in.")


def login_user(username: str, password: str):
    """Authenticate a user and store JWT in session."""
    user = users_collection.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        user_id = str(user["_id"])
        st.session_state["jwt_token"] = generate_jwt(user_id, username)
        st.session_state["user"] = user
        st.success(f"✅ Welcome back, {username}!")
        st.rerun()
    else:
        st.error("❌ Invalid username or password. Please try again.")


@st.cache_data(ttl=600)
def get_user(_user_id: ObjectId):
    """Fetch user by ID from MongoDB."""
    return users_collection.find_one({"_id": _user_id})


# ---------------------------
#   Profile Page
# ---------------------------
def user_profile(user_id: str):
    """Render the logged-in user's profile page."""
    try:
        _user_id = ObjectId(user_id)
    except Exception:
        st.error("❌ Invalid user ID.")
        return

    user = get_user(_user_id)

    if not user:
        st.error("⚠️ User not found.")
        return

    st.write(f"👋 Hi, **{user['username']}**")
    st.image(user["picture"], width=100)
    st.write(f"📧 {user['email']}")

    if st.button("🚪 Logout", use_container_width=True):
        logout()


# ---------------------------
#   Main Page Controller
# ---------------------------
st.title("👩‍🎓 User Authentication System")

if "jwt_token" not in st.session_state:
    login_page()
else:
    user_id = verify_jwt_token(st.session_state["jwt_token"])
    if user_id:
        user_profile(user_id)
    else:
        del st.session_state["jwt_token"]
        st.rerun()
