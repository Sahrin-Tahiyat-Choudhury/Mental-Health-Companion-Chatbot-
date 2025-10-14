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
if "reflection_temp" not in st.session_state:
    st.session_state.reflection_temp = ""
if "input_temp" not in st.session_state:
    st.session_state.input_temp = ""

# -----------------------------
# App Layout
# -----------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

tabs = st.tabs(["💬 Chat", "📊 Mood Overview", "✍ Self-Reflection", "⚙ Settings"])

# -----------------------------
# ⚙ Settings Tab
# -----------------------------
with tabs[3]:
    st.header("⚙ Settings")

    nickname_input = st.text_input("Set AI Nickname:", value=st.session_state.nickname, key="nickname_input_box")

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

    user_input = st.text_input("You:", key="input_temp", placeholder="Type your message...")

    if st.button("Send", key="send_button"):
        if user_input.strip():
            prompt = f"""
            You are a calm, compassionate AI companion named {st.session_state.nickname}.
            Respond in a short, gentle, and supportive way (2–3 sentences max).
            Avoid medical or personal advice.
            User: {user_input}
            """
            reply = model.generate_content(prompt).text

            mood_prompt = f"""
            Determine the mood of this message. Respond with one word:
            Happy, Sad, Stressed, Anxious, Neutral, Excited
            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            st.session_state.history.append({"user": user_input, "reply": reply, "mood": mood})
            db.reference("chat_history").set(st.session_state.history)

            st.session_state.input_temp = ""
            st.rerun()
        else:
            st.warning("⚠ Please type something before sending.")

# -----------------------------
# 📊 Mood Overview Tab
# -----------------------------
with tabs[1]:
    st.header("📊 Mood Overview")

    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        fig = px.bar(mood_counts, x=mood_counts.index, y=mood_counts.values,
                     labels={'x': 'Mood', 'y': 'Count'}, title="Mood Frequency Chart")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No chat data yet. Your mood chart will appear here after chatting.")

# -----------------------------
# ✍ Self-Reflection Tab
# -----------------------------
with tabs[2]:
    st.header("✍ Self-Reflection")

    reflection_text = st.text_area("Write your reflection:", key="reflection_temp", placeholder="Write your thoughts here...")

    if st.button("💾 Save Reflection"):
        if reflection_text.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.reflection_entries.append({"time": timestamp, "text": reflection_text})
            st.success("✅ Reflection saved!")
            st.session_state.reflection_temp = ""
            st.rerun()
        else:
            st.warning("⚠ Please write something before saving.")

    if st.session_state.reflection_entries:
        st.write("### 📜 Your Saved Reflections")
        for idx, entry in enumerate(st.session_state.reflection_entries):
            st.markdown(f"🕒 {entry['time']}")
            st.write(entry['text'])
            if st.button(f"🗑 Delete ({entry['time']})", key=f"del_{idx}"):
                st.session_state.reflection_entries.pop(idx)
                st.rerun()
