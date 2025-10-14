import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import datetime
import plotly.express as px

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
    try:
        cred = credentials.Certificate(firebase_key_dict)
        firebase_admin.initialize_app(cred, {"databaseURL": firebase_db_url})
    except ValueError:
        # Already initialized
        pass

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
tabs = st.tabs(["💬 Chat", "📊 Mood Overview", "✍ Self-Reflection", "⚙ Settings"])

# -----------------------------
# Settings Tab
# -----------------------------
with tabs[3]:
    st.header("⚙ Settings")
    nickname_input = st.text_input("Set AI Nickname:", value=st.session_state.nickname)
    if st.button("Save Nickname"):
        st.session_state.nickname = nickname_input
        st.success(f"AI nickname updated to {st.session_state.nickname}!")

# -----------------------------
# Chat Tab
# -----------------------------
with tabs[0]:
    st.header(f"💬 Chat with {st.session_state.nickname}")

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history.clear()
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Chat messages
    chat_container = st.container()
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
        st.markdown(f"**You:** {user_msg}")
        st.markdown(f"**{st.session_state.nickname}:** {ai_msg}")
        st.markdown(f"**Detected Mood: {mood} {mood_emoji}**")
        st.markdown("---")

    # Chat input using form to avoid API exceptions
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message:")
        submit_button = st.form_submit_button("Send")

        if submit_button and user_input.strip():
            # AI reply
            prompt = f"""
            You are a calm, compassionate AI companion named {st.session_state.nickname}.
            Respond gently, neutrally, and supportively. Avoid inappropriate topics.
            User: {user_input}
            """
            reply = model.generate_content(prompt).text.strip()

            # Mood detection
            mood_prompt = f"""
            Determine the user's mood (one word): Happy, Sad, Stressed, Anxious, Neutral, Excited.
            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            # Save to session & Firebase
            st.session_state.history.append({
                "user": user_input,
                "reply": reply,
                "mood": mood
            })
            db.reference("chat_history").set(st.session_state.history)

# -----------------------------
# Mood Overview Tab
# -----------------------------
with tabs[1]:
    st.header("📊 Mood Overview")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
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
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.reflection_entries.append({"time": timestamp, "text": reflection_text})
            st.success("Reflection saved!")
            st.experimental_rerun()
        else:
            st.warning("Write something before saving!")

    if st.session_state.reflection_entries:
        st.subheader("📝 Your Reflections")
        for idx, entry in enumerate(st.session_state.reflection_entries):
            with st.expander(f"Reflection from {entry['time']}"):
                st.write(entry["text"])
                if st.button("Delete", key=f"del_ref_{idx}"):
                    st.session_state.reflection_entries.pop(idx)
                    st.success("Deleted!")
                    st.experimental_rerun()


