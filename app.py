import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# -------------------- Load Secrets --------------------
load_dotenv()  # local env variables
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
firebase_key_dict = st.secrets.get("FIREBASE_KEY_JSON")
firebase_url = st.secrets.get("FIREBASE_DB_URL") or os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_key_dict))
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="CalmMate - AI Companion", page_icon="💬", layout="wide")

# Use tabs for better UI
tab1, tab2 = st.tabs(["💬 Chat", "📊 Mood Chart"])

# -------------------- Initialize Session --------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------- Helper Functions --------------------
def generate_reply(user_input):
    # CalmMate reply
    prompt = f"""
    You are a calm, compassionate AI companion. Respond in a gentle, neutral, supportive way.
    Do not offer medical advice or unsafe topics. Keep it concise (2–3 sentences).

    User: {user_input}
    """
    reply = model.generate_content(prompt).text

    # Detect mood
    mood_prompt = f"""
    Determine the mood of this user message. Respond with ONE word only:
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {user_input}
    """
    mood = model.generate_content(mood_prompt).text.strip()
    return reply, mood

def save_to_firebase(history):
    db.reference("chat_history").set(history)

# -------------------- Tab 1: Chat --------------------
with tab1:
    st.header("💬 Chat with CalmMate")
    st.markdown("Your messages will appear instantly below. Start typing!")

    # Display existing chat
    for chat in st.session_state.history:
        with st.chat_message("user"):
            st.markdown(chat["user"])
        with st.chat_message("assistant"):
            st.markdown(chat["reply"])
            mood_emoji = {
                "Happy": "😊",
                "Sad": "😢",
                "Stressed": "😟",
                "Anxious": "😰",
                "Neutral": "😐",
                "Excited": "😃"
            }.get(chat["mood"], "😐")
            st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}")

    # Input at bottom
    user_input = st.chat_input("Type your message here...")

    if user_input:
        reply, mood = generate_reply(user_input)
        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        save_to_firebase(st.session_state.history)

        # Display instantly
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            st.markdown(reply)
            mood_emoji = {
                "Happy": "😊",
                "Sad": "😢",
                "Stressed": "😟",
                "Anxious": "😰",
                "Neutral": "😐",
                "Excited": "😃"
            }.get(mood, "😐")
            st.markdown(f"Detected Mood: {mood} {mood_emoji}")

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

# -------------------- Tab 2: Mood Chart --------------------
with tab2:
    st.header("📊 Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        # Assign colors per mood
        color_map = {
            "Happy": "#FFD700",      # gold
            "Sad": "#1E90FF",        # dodger blue
            "Stressed": "#FF4500",   # orange red
            "Anxious": "#8A2BE2",    # blue violet
            "Neutral": "#A9A9A9",    # dark grey
            "Excited": "#32CD32"     # lime green
        }
        chart_colors = [color_map.get(m, "#FFFFFF") for m in mood_counts.index]

        st.bar_chart(pd.DataFrame({"Count": mood_counts.values}, index=mood_counts.index), use_container_width=True)
    else:
        st.info("No chat history yet. Start chatting to see your mood trends!")
