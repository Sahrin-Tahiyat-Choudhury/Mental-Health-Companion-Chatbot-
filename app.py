import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from firebase_admin import credentials, db, initialize_app
import firebase_admin

# ======================
# Page config
# ======================
st.set_page_config(
    page_title="Mental Health Companion",
    page_icon="💬",
    layout="wide"
)

# ======================
# Dark mode CSS
# ======================
st.markdown(
    """
    <style>
    body {background-color: #0D0D0D; color: #FFFFFF;}
    .stButton>button {background-color: #333333; color: #FFFFFF;}
    .stTextInput>div>div>input {background-color: #1C1C1C; color: #FFFFFF; border: 1px solid #333333;}
    hr {border: 1px solid #333333;}
    </style>
    """,
    unsafe_allow_html=True
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
# Session State
# ======================
if "history" not in st.session_state:
    st.session_state.history = []

# ======================
# Functions
# ======================
def detect_mood(text):
    prompt = f"""
    Determine the mood of this user message. Respond with only ONE of these words: 
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {text}
    """
    response = model.generate_content(prompt)
    return str(response.text.strip())

def save_to_firebase(chat_list):
    ref = db.reference("chat_history")
    ref.set(chat_list)

def generate_reply(user_input):
    prompt = f"""
    You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
    Do not offer medical advice. Avoid inappropriate or unsafe topics.
    Keep the message concise (2–3 sentences).

    User: {user_input}
    """
    reply = str(model.generate_content(prompt).text)
    mood = detect_mood(user_input)
    chat_entry = {"user": str(user_input), "reply": reply, "mood": mood}
    st.session_state.history.append(chat_entry)
    save_to_firebase(st.session_state.history)
    return reply, mood

# ======================
# Tabs
# ======================
tab1, tab2 = st.tabs(["💬 Chat", "📊 Mood Stats"])

# ===== CHAT TAB =====
with tab1:
    st.header("💬 Chat with CalmMate")
    st.markdown("Share how you're feeling today. CalmMate will reply with empathy and care.")

    chat_container = st.container()

    # Display chat in a scrollable container
    with chat_container:
        for chat in st.session_state.history:
            # User bubble
            st.markdown(
                f"<div style='background-color:#2E2E2E;color:#FFFFFF;padding:10px;border-radius:12px;margin:6px 0;width:60%;'>"
                f"<b>You:</b> {chat['user']}</div>",
                unsafe_allow_html=True
            )
            # CalmMate bubble
            st.markdown(
                f"<div style='background-color:#1F3B3B;color:#FFFFFF;padding:10px;border-radius:12px;margin:6px 0;width:60%;'>"
                f"<b>CalmMate:</b> {chat['reply']}</div>",
                unsafe_allow_html=True
            )
            # Mood
            mood_emoji = {
                "Happy": "😊",
                "Sad": "😢",
                "Stressed": "😟",
                "Anxious": "😰",
                "Neutral": "😐",
                "Excited": "😃"
            }.get(chat["mood"], "😐")
            st.markdown(
                f"<small style='color:#CCCCCC'><b>Mood Detected:</b> {chat['mood']} {mood_emoji}</small>",
                unsafe_allow_html=True
            )
            st.markdown("<hr>", unsafe_allow_html=True)

    # Input at bottom
    user_input = st.chat_input("Type your message here...")
    if user_input:
        generate_reply(user_input)
        st.experimental_rerun()  # auto-refresh chat

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")
        st.experimental_rerun()

# ===== MOOD STATS TAB =====
with tab2:
    st.header("📊 Mood Trend")
    if st.session_state.history:
        mood_counts = pd.Series([str(c["mood"]) for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat yet. Start a conversation to see mood trends!")
