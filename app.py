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

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Chat messages
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

    # Chat input
    user_input = st.text_input("You:", key="input_box")
    if st.button("Send", key="send_button") and user_input.strip() != "":
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

        # Save to session & Firebase
        st.session_state.history.append({"user": user_input, "reply": reply, "mood": mood})
        db.reference("chat_history").set(st.session_state.history)

        # Clear input
        st.session_state.input_box = ""

# -----------------------------
# Mood Overview Tab
# -----------------------------
with tabs[1]:
    st.header("📊 Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat data yet. Your mood chart will appear here after chatting.")

# -----------------------------
# Self-Reflection Tab
# -----------------------------
with tabs[2]:
    st.header("✍ Self-Reflection")
    reflection_text = st.text_area("Write your thoughts here:", key="reflection_box")
    if st.button("Save Reflection"):
        if reflection_text.strip():
            st.session_state.reflection_entries.append(reflection_text)
            st.success("Reflection saved!")
            st.session_state.reflection_box = ""

    if st.session_state.reflection_entries:
        for idx, entry in enumerate(st.session_state.reflection_entries):
            st.markdown(f"*Entry {idx+1}:* {entry}")
            if st.button(f"Delete Entry {idx+1}", key=f"del_{idx}"):
                st.session_state.reflection_entries.pop(idx)
                st.success("Deleted!")
                st.experimental_rerun()
