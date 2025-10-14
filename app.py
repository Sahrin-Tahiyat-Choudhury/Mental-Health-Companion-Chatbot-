import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import datetime

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_url = os.getenv("FIREBASE_DB_URL")  # add this in .env

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# Streamlit page config
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="centered")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []

# Nickname input for AI
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

nickname = st.text_input("Set AI Nickname:", value=st.session_state.nickname)
st.session_state.nickname = nickname

# Tabs: Chat, Mood Overview, Self-Reflection
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self-Reflection"])

# Helper functions
def detect_mood(text):
    prompt = f"""
    Determine the mood of this user message. Respond with only ONE of these words:
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def save_to_firebase(ref_name, data):
    ref = db.reference(ref_name)
    ref.set(data)

# ------------------- Chat Tab -------------------
with tab1:
    st.header(f"Chat with {nickname}")

    chat_placeholder = st.container()

    user_input = st.text_input("You:", placeholder="Type your message here...")

    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = []
        save_to_firebase("chat_history", st.session_state.chat_history)
        chat_placeholder.empty()

    if user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond gently.
        Avoid inappropriate or unsafe topics. Keep it 2-3 sentences.

        User: {user_input}
        """
        reply = model.generate_content(prompt).text
        mood = detect_mood(user_input)

        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.chat_history.append(chat_entry)
        save_to_firebase("chat_history", st.session_state.chat_history)

    # Display chat
    with chat_placeholder:
        for chat in st.session_state.chat_history:
            st.markdown(f"<div style='text-align:right; background-color:#1f1f1f; color:#f5f5f5; padding:8px; border-radius:8px;'>You: {chat['user']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align:left; background-color:#333333; color:#ffffff; padding:8px; border-radius:8px;'> {nickname}: {chat['reply']}</div>", unsafe_allow_html=True)
            st.markdown(f"Detected Mood: {chat['mood']}")
            st.markdown("---")

# ------------------- Mood Overview Tab -------------------
with tab2:
    st.header("📊 Mood Overview")
    if st.session_state.chat_history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.chat_history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("Your mood stats will appear here after chatting.")

# ------------------- Self-Reflection Tab -------------------
with tab3:
    st.header("📝 Self-Reflection")

    reflection_input = st.text_area("Write your thoughts here...")
    if st.button("💾 Save Reflection"):
        if reflection_input.strip():
            mood = detect_mood(reflection_input)
            entry = {"text": reflection_input, "time": str(datetime.datetime.now()), "mood": mood}
            st.session_state.journal_entries.append(entry)
            save_to_firebase("journal_entries", st.session_state.journal_entries)
            st.success("Reflection saved!")
        else:
            st.warning("Please write something before saving.")

    st.subheader("Your Past Reflections")
    for idx, entry in enumerate(reversed(st.session_state.journal_entries)):
        st.markdown(f"Time: {entry['time']}")
        st.markdown(f"Mood: {entry['mood']}")
        st.markdown(f"> {entry['text']}")
        if st.button(f"🗑 Delete Entry {idx}"):
            real_idx = len(st.session_state.journal_entries) - 1 - idx
            st.session_state.journal_entries.pop(real_idx)
            save_to_firebase("journal_entries", st.session_state.journal_entries)
            st.experimental_rerun()
        st.markdown("---")
