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
# Gemini API Key
api_key = st.secrets["GOOGLE_API_KEY"]

# Firebase
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
    return response.text.strip()

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
    reply = model.generate_content(prompt).text
    mood = detect_mood(user_input)
    chat_entry = {"user": user_input, "reply": reply, "mood": mood}
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

    # Display chat history as bubbles
    for chat in st.session_state.history:
        # User message
        st.markdown(f"<div style='background-color:#D0E6FF;padding:8px;border-radius:10px'><b>You:</b> {chat['user']}</div>", unsafe_allow_html=True)
        # AI message
        st.markdown(f"<div style='background-color:#D0FFD6;padding:8px;border-radius:10px'><b>CalmMate:</b> {chat['reply']}</div>", unsafe_allow_html=True)
        # Mood
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")
        st.markdown(f"<small><b>Mood Detected:</b> {chat['mood']} {mood_emoji}</small>", unsafe_allow_html=True)
        st.markdown("---")

    # Input at the bottom
    user_input = st.chat_input("Type your message here...")
    if user_input:
        reply, mood = generate_reply(user_input)
        st.experimental_rerun()  # update UI instantly

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")
        st.experimental_rerun()

# ===== MOOD STATS TAB =====
with tab2:
    st.header("📊 Mood Trend")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat yet. Start a conversation to see mood trends!")
