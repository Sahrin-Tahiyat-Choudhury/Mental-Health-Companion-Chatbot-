import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Initialize Firebase safely
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
cred = credentials.Certificate(firebase_key_dict)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# -------------------------------
# Streamlit UI Settings
# -------------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# Tabs
tabs = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self-Reflection"])

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "reflections" not in st.session_state:
    st.session_state.reflections = []
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

# -------------------------------
# Nickname input
# -------------------------------
with tabs[0]:
    nickname_input = st.text_input("Set AI Nickname:", value=st.session_state.nickname)
    if nickname_input.strip():
        st.session_state.nickname = nickname_input.strip()

# -------------------------------
# Handle user input
# -------------------------------
def handle_input():
    user_input = st.session_state.input_box
    if user_input.strip() == "":
        return

    # Generate AI reply
    prompt = f"""
    You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
    Do not offer medical advice. Avoid inappropriate or unsafe topics.
    Keep the message concise (2–3 sentences).
    User: {user_input}
    """
    reply = model.generate_content(prompt).text

    # Mood detection
    mood_prompt = f"""
    Determine the mood of this user message. Respond with only ONE of these words:
    Happy, Sad, Stressed, Anxious, Neutral, Excited
    Message: {user_input}
    """
    mood = model.generate_content(mood_prompt).text.strip()

    # Save chat
    chat_entry = {"user": user_input, "reply": reply, "mood": mood}
    st.session_state.history.append(chat_entry)
    db.reference("chat_history").set(st.session_state.history)

    # Clear input box safely
    st.session_state.input_box = ""

# -------------------------------
# Chat Tab
# -------------------------------
with tabs[0]:
    # Scrollable chat
    chat_container = st.container()
    st.text_input("You:", key="input_box", placeholder="Type your message here...", on_change=handle_input)

    with chat_container:
        for chat in st.session_state.history:
            # Color formatting
            user_color = "background-color:#1e1e1e; color:white; padding:8px; border-radius:8px; text-align:right;"
            ai_color = "background-color:#2d2d2d; color:#a0e0ff; padding:8px; border-radius:8px; text-align:left;"

            st.markdown(f"<div style='{user_color}'><b>You:</b> {chat['user']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='{ai_color}'><b>{st.session_state.nickname}:</b> {chat['reply']}</div>", unsafe_allow_html=True)
            st.markdown("---", unsafe_allow_html=True)

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})

# -------------------------------
# Mood Overview Tab
# -------------------------------
with tabs[1]:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("Chat first to see mood overview.")

# -------------------------------
# Self-Reflection Tab
# -------------------------------
with tabs[2]:
    def save_reflection():
        text = st.session_state.reflection_box
        if text.strip():
            st.session_state.reflections.append({"text": text.strip()})
            st.success("Saved!")
            st.session_state.reflection_box = ""  # Reset safely via callback

    st.text_area("Write your reflection here:", key="reflection_box")
    st.button("💾 Save Reflection", on_click=save_reflection)

    if st.session_state.reflections:
        st.markdown("### Saved Reflections")
        for idx, ref in enumerate(st.session_state.reflections):
            st.write(ref["text"])
            if st.button(f"🗑 Delete", key=f"del_{idx}"):
                st.session_state.reflections.pop(idx)
                st.experimental_rerun()
