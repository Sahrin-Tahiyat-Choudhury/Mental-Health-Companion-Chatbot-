import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

# -----------------------------
# Load secrets and initialize
# -----------------------------
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
firebase_db_url = st.secrets["FIREBASE_DATABASE_URL"]

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_db_url})

# -----------------------------
# Initialize session states
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"
if "reflection_entries" not in st.session_state:
    st.session_state.reflection_entries = []
if "input_value" not in st.session_state:
    st.session_state.input_value = ""
if "reflection_value" not in st.session_state:
    st.session_state.reflection_value = ""

# -----------------------------
# App Layout
# -----------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# Tabs
tabs = st.tabs(["💬 Chat", "📊 Mood Overview", "✍ Self-Reflection", "⚙ Settings"])

# -----------------------------
# Settings Tab
# -----------------------------
with tabs[3]:
    st.header("Settings")
    st.text_input("Set AI Nickname:", value=st.session_state.nickname, key="nickname_input")
    if st.button("Save Nickname"):
        st.session_state.nickname = st.session_state.nickname_input
        st.success(f"AI nickname updated to {st.session_state.nickname}!")

# -----------------------------
# Chat Tab
# -----------------------------
with tabs[0]:
    st.header("💬 Chat with " + st.session_state.nickname)

    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    chat_container = st.container()
    with chat_container:
        for chat in reversed(st.session_state.history):
            user_msg = chat["user"]
            ai_msg = chat["reply"]
            mood = chat["mood"]
            mood_emoji = {
                "Happy": "😊",
                "Sad": "😢",
                "Stressed": "😟",
                "Anxious": "😰",
                "Neutral": "😐",
                "Excited": "😃"
            }.get(mood, "😐")
            st.markdown(f"*You:* {user_msg}")
            st.markdown(f"{st.session_state.nickname}:** {ai_msg}")
            st.markdown(f"Detected Mood: {mood} {mood_emoji}")
            st.markdown("---")

    # Chat input field
    user_input = st.text_input("You:", value=st.session_state.input_value, key="input_box")

    # Send message
    if st.button("Send", key="send_button"):
        if user_input.strip():
            prompt = f"""
            You are a calm, compassionate AI companion. Respond gently, neutrally, and supportively.
            Avoid medical advice or inappropriate topics. Keep concise (2–3 sentences).
            User: {user_input}
            """
            reply = model.generate_content(prompt).text

            # Mood detection
            mood_prompt = f"""
            Determine the mood of this user message. Respond with only one word:
            Happy, Sad, Stressed, Anxious, Neutral, Excited
            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            # Save to session and Firebase
            st.session_state.history.append({"user": user_input, "reply": reply, "mood": mood})
            db.reference("chat_history").set(st.session_state.history)

            # Clear input safely and refresh
            st.session_state.input_value = ""
            st.rerun()


# -----------------------------
# Self-Reflection Tab
# -----------------------------
import datetime

with tabs[2]:
    st.header("✍ Self-Reflection")
    reflection_text = st.text_area("Write your thoughts here:", value=st.session_state.reflection_value, key="reflection_box")

    if st.button("Save Reflection"):
        if reflection_text.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            st.session_state.reflection_entries.append({
                "text": reflection_text,
                "time": timestamp
            })
            st.success("Reflection saved!")
            st.session_state.reflection_value = ""
            st.rerun()

    if st.session_state.reflection_entries:
        for idx, entry in enumerate(reversed(st.session_state.reflection_entries)):
            st.markdown(f"🕒 {entry['time']}")
            st.markdown(entry["text"])
            if st.button(f"Delete This Reflection", key=f"del_{idx}"):
                st.session_state.reflection_entries.pop(len(st.session_state.reflection_entries) - 1 - idx)
                st.rerun()
            st.markdown("---")
