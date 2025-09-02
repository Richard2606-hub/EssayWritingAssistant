import bcrypt
import sys, os
import streamlit as st
from bson import ObjectId

# Internal imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Connection import get_collection
from Authentication import generate_jwt, verify_jwt_token, logout

# Initialize MongoDB collection
users_collection = get_collection("users")

# --- Main auth UI ---
def login_page():
    """Render the Register/Login tabs."""
    tab1, tab2 = st.tabs(["Register", "Login"])
    with tab1:
        register_tab()
    with tab2:
        login_tab()

# --- Register ---
def register_tab():
    st.header("Register")
    username = st.text_input("Username", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Register"):
        register_user(username, email, password)

def register_user(username: str, email: str, password: str):
    """Handle user registration with validation."""
    if not username or not email or not password:
        st.error("⚠️ Please fill in all the fields.")
        return

    if users_collection.find_one({"username": username}):
        st.error("⚠️ Username already exists.")
        return

    if users_collection.find_one({"email": email}):
        st.error("⚠️ Email already exists.")
        return

    try:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        users_collection.insert_one({
            "username": username,
            "password": hashed_password,
            "email": email,
            "picture": "https://www.shutterstock.com/image-vector/blank-avatar-photo-place-holder-600nw-1114445501.jpg"
        })
        st.success("✅ Registration successful! You can now log in.")
    except Exception as e:
        st.error(f"❌ Failed to register: {e}")

# --- Login ---
def login_tab():
    st.header("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        login_user(username, password)

def login_user(username: str, password: str):
    """Authenticate user and set session."""
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        st.session_state["jwt_token"] = generate_jwt(str(user["_id"]), username)
        st.session_state["user"] = user
        st.rerun()
    else:
        st.error("❌ Invalid username or password.")

# --- Caching helper ---
@st.cache_data(ttl=600)
def get_user(user_id: ObjectId):
    return users_collection.find_one({"_id": user_id})

# --- Profile page ---
def user_profile(user_id: str):
    """Render user profile with logout button."""
    try:
        _user_id = ObjectId(user_id)
        user = get_user(_user_id)
    except Exception:
        st.error("❌ Invalid user session. Please log in again.")
        logout()
        return

    if not user:
        st.error("❌ User not found.")
        logout()
        return

    st.write(f"👋 Hi, **{user['username']}**")
    st.image(user["picture"], width=100)
    st.write(f"📧 {user['email']}")

    if st.button("Logout"):
        logout()

# --- Entrypoint ---
st.title("🔑 User Authentication System")

if "jwt_token" not in st.session_state:
    login_page()
else:
    user_id = verify_jwt_token(st.session_state["jwt_token"])
    if user_id:
        user_profile(user_id)
    else:
        if "jwt_token" in st.session_state:
            del st.session_state["jwt_token"]
        st.rerun()
