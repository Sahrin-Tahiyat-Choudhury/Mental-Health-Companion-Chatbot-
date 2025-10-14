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
if "input_box" not in st.session_state:
    st.session_state.input_box = ""
if "reflection_box" not in st.session_state:
    st.session_state.reflection_box = ""

# -----------------------------
# App Layout
# -----------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

tabs = st.tabs(["💬 Chat", "📈 Mood Overview", "✍ Self-Reflection", "⚙ Settings"])

# -----------------------------
# ⚙ Settings Tab
# -----------------------------
with tabs[3]:
    st.header("⚙ Settings")
    nickname_input = st.text_input("Set AI Nickname:", value=st.session_state.nickname, key="nickname_input")
    if st.button("Save Nickname"):
        st.session_state.nickname = nickname_input
        st.success(f"AI nickname updated to {st.session_state.nickname}!")

# -----------------------------
# 💬 Chat Tab
# -----------------------------
with tabs[0]:
    st.header(f"💬 Chat with {st.session_state.nickname}")

    if st.button("🗑 Clear Chat"):
        st.session_state.history.clear()
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Show conversation
    chat_placeholder = st.container()
    for chat in st.session_state.history:
        st.markdown(f"*You:* {chat['user']}")
        st.markdown(f"{st.session_state.nickname}:** {chat['reply']}")
        st.markdown(f"Detected Mood: {chat['mood']}")
        st.markdown("---")

    # Input box and send
    user_input = st.text_input("Type your message:", value=st.session_state.input_box, key="input_text")

    if st.button("Send"):
        if user_input.strip():
            prompt = f"""
            You are a compassionate AI companion named {st.session_state.nickname}.
            Respond gently, in 2–3 sentences, avoiding medical or inappropriate advice.
            User: {user_input}
            """
            reply = model.generate_content(prompt).text.strip()

            mood_prompt = f"""
            Determine the user's mood (one word): Happy, Sad, Stressed, Anxious, Neutral, or Excited.
            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.history.append({"time": timestamp, "user": user_input, "reply": reply, "mood": mood})
            db.reference("chat_history").set(st.session_state.history)

            st.session_state.input_box = ""  # clear text input
            st.rerun()
        else:
            st.warning("Please type something before sending!")

# -----------------------------
# 📈 Mood Overview Tab
# -----------------------------
with tabs[1]:
    st.header("📈 Mood Overview")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        df["time"] = pd.to_datetime(df["time"])
        fig = px.bar(df, x="time", y="mood", title="Mood Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet. Chat to generate your mood chart.")

# -----------------------------
# ✍ Self-Reflection Tab
# -----------------------------
with tabs[2]:
    st.header("✍ Self-Reflection")

    reflection_text = st.text_area("Write your thoughts here:", value=st.session_state.reflection_box, key="reflection_text")
    if st.button("Save Reflection"):
        if reflection_text.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.reflection_entries.append({"time": timestamp, "text": reflection_text})
            st.session_state.reflection_box = ""
            st.success("Reflection saved!")
            st.rerun()
        else:
            st.warning("Write something before saving!")

    if st.session_state.reflection_entries:
        st.subheader("📝 Your Reflections")
        for idx, entry in enumerate(st.session_state.reflection_entries):
            with st.expander(f"Reflection from {entry['time']}"):
                st.write(entry['text'])
                if st.button("Delete", key=f"del_ref_{idx}"):
                    st.session_state.reflection_entries.pop(idx)
                    st.success("Deleted!")
                    st.rerun()
