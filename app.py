import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_url = os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# -----------------------------
# Streamlit UI & Styling
# -----------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #121212;
        color: #f0f0f0;
    }
    .chat-user {
        background-color: #1f1f1f;
        color: #f0f0f0;
        padding: 8px;
        border-radius: 8px;
        text-align: right;
        margin-bottom: 4px;
    }
    .chat-ai {
        background-color: #272727;
        color: #f0f0f0;
        padding: 8px;
        border-radius: 8px;
        text-align: left;
        margin-bottom: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar: AI Nickname
nickname = st.sidebar.text_input("Enter AI Nickname:", value="CalmMate")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# -----------------------------
# Tabs: Chat & Mood Overview
# -----------------------------
tab_chat, tab_mood = st.tabs(["💬 Chat", "📊 Mood Overview"])

# -----------------------------
# Chat Tab
# -----------------------------
with tab_chat:
    chat_container = st.container()

    # Clear Chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # -----------------------------
    # Display Chat History (Above Input)
    # -----------------------------
    for chat in st.session_state.history:
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")
        st.markdown(f"<div class='chat-user'>You: {chat['user']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-ai'>{nickname}: {chat['reply']}</div>", unsafe_allow_html=True)
        st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}", unsafe_allow_html=True)
        st.markdown("---")

    # -----------------------------
    # Input Form at Bottom
    # -----------------------------
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type your message...")
        submitted = st.form_submit_button("Send")

        if submitted and user_input:
            # Generate AI reply
            prompt = f"""
            You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
            Do not offer medical advice. Avoid inappropriate or unsafe topics.
            Keep the message concise (2–3 sentences).

            User: {user_input}
            """
            with st.spinner("Thinking..."):
                reply = model.generate_content(prompt).text

            # Detect Mood
            mood_prompt = f"""
            Determine the mood of this user message. Respond with ONLY ONE of these words:
            Happy, Sad, Stressed, Anxious, Neutral, Excited

            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            # Save to session and Firebase
            chat_entry = {"user": user_input, "reply": reply, "mood": mood}
            st.session_state.history.append(chat_entry)
            db.reference("chat_history").set(st.session_state.history)

            st.experimental_rerun()  # Automatically refresh chat to show latest message

# -----------------------------
# Mood Overview Tab
# -----------------------------
with tab_mood:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("Chat some messages first to see mood overview.")
