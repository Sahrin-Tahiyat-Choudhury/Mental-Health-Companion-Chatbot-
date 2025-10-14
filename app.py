import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import datetime
import plotly.express as px
import uuid  # for unique keys

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

# Dynamic keys to prevent API exception
def get_new_key(prefix: str):
    return f"{prefix}_{uuid.uuid4().hex[:6]}"

# -----------------------------
# App Layout
# -----------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")
tabs = st.tabs(["💬 Chat", "📈 Mood Trend", "✍ Self-Reflection", "⚙ Settings"])

# -----------------------------
# ⚙ Settings Tab
# -----------------------------
with tabs[3]:
    st.header("⚙ Settings")
    nickname_input = st.text_input("Set AI Nickname:", value=st.session_state.nickname, key=get_new_key("nick"))
    if st.button("Save Nickname"):
        st.session_state.nickname = nickname_input
        st.success(f"AI nickname updated to *{st.session_state.nickname}*!")
        st.rerun()

# -----------------------------
# 💬 Chat Tab
# -----------------------------
with tabs[0]:
    st.header(f"💬 Chat with {st.session_state.nickname}")

    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")
        st.rerun()

    chat_container = st.container()
    with chat_container:
        for chat in reversed(st.session_state.history):
            user_msg = chat["user"]
            ai_msg = chat["reply"]
            mood = chat["mood"]
            mood_emoji = {
                "Happy": "😊", "Sad": "😢", "Stressed": "😟",
                "Anxious": "😰", "Neutral": "😐", "Excited": "😃"
            }.get(mood, "😐")
            st.markdown(f"*You:* {user_msg}")
            st.markdown(f"{st.session_state.nickname}:** {ai_msg}")
            st.markdown(f"Detected Mood: {mood} {mood_emoji}")
            st.markdown("---")

    # Use dynamic key to reset safely
    user_input = st.text_input("You:", key=get_new_key("chat_input"), placeholder="Type your message...")

    if st.button("Send", key=get_new_key("send_btn")):
        if user_input.strip():
            prompt = f"""
            You are a calm, compassionate AI companion named {st.session_state.nickname}.
            Respond gently, briefly (2–3 sentences max), and supportively.
            Avoid personal or medical advice.
            User: {user_input}
            """
            reply = model.generate_content(prompt).text

            mood_prompt = f"""
            Determine the user's mood (one word only): Happy, Sad, Stressed, Anxious, Neutral, or Excited.
            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.history.append({"time": timestamp, "user": user_input, "reply": reply, "mood": mood})
            db.reference("chat_history").set(st.session_state.history)
            st.rerun()
        else:
            st.warning("⚠ Please type something before sending.")

# -----------------------------
# 📈 Mood Trend Tab
# -----------------------------
with tabs[1]:
    st.header("📈 Mood Trend Over Time")

    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        df['time'] = pd.to_datetime(df['time'])
        fig = px.line(df, x='time', y='mood', title="Mood Trend Over Time", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No chat data yet. Your mood trend will appear here after chatting.")

# -----------------------------
# ✍ Self-Reflection Tab
# -----------------------------
with tabs[2]:
    st.header("✍ Self-Reflection")

    reflection_text = st.text_area("Write your reflection:", key=get_new_key("reflection_box"), placeholder="Write your thoughts here...")

    if st.button("💾 Save Reflection", key=get_new_key("save_btn")):
        if reflection_text.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.reflection_entries.append({"time": timestamp, "text": reflection_text})
            st.success("✅ Reflection saved!")
            st.rerun()
        else:
            st.warning("⚠ Please write something before saving.")

    if st.session_state.reflection_entries:
        st.write("### 📜 Your Saved Reflections")
        for idx, entry in enumerate(reversed(st.session_state.reflection_entries)):
            st.markdown(f"🕒 {entry['time']}")
            st.write(entry['text'])
            if st.button(f"🗑 Delete ({entry['time']})", key=get_new_key(f"del_{idx}")):
                st.session_state.reflection_entries.pop(len(st.session_state.reflection_entries) - 1 - idx)
                st.rerun()
