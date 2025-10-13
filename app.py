import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from firebase_admin import credentials, db, initialize_app
import firebase_admin

# ======================
# Streamlit page config
# ======================
st.set_page_config(
    page_title="Mental Health Companion",
    page_icon="💬",
    layout="wide"
)

# ======================
# Load Secrets
# ======================
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
firebase_url = st.secrets["FIREBASE_DB_URL"]

# ======================
# Configure Gemini
# ======================
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# ======================
# Initialize Firebase
# ======================
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    initialize_app(cred, {"databaseURL": firebase_url})

# ======================
# Initialize Session State
# ======================
if "history" not in st.session_state:
    st.session_state
