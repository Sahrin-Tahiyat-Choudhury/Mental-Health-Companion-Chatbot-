import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# Load environment variables
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

# Streamlit UI
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

# Sidebar for nickname
nickname = st.sidebar.text_input("Enter AI Nickname:", value="CalmMate")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Tabs: Chat and Mood Overview
tab_chat, tab_mood = st.tabs(["💬 Chat", "📊 Mood Overview"])

with tab_chat:
    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Chat input
    user_input = st.text_input("You:", placeholder="Type here...")

    def detect_mood(text):
        prompt = f"""
        Determine the mood of this user message. Respond with only ONE of these words:
        Happy, Sad, Stressed, Anxious, Neutral, Excited

        Message: {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip()

    def save_to_firebase(chat_list):
        """Save entire session history to Firebase"""
        ref = db.reference("chat_history")
        ref.set(chat_list)

    if user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
        Do not offer medical advice. Avoid inappropriate or unsafe topics.
        Keep the message concise (2–3 sentences).

        User: {user_input}
        """
        with st.spinner("Thinking..."):
            reply = model.generate_content(prompt).text

        mood = detect_mood(user_input)
        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        save_to_firebase(st.session_state.history)

    # Display chat history
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

with tab_mood:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("Chat some messages first to see mood overview.")
