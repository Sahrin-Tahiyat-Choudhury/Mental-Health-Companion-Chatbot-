import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_url = os.getenv("FIREBASE_DATABASE_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_KEY_JSON"]))
    firebase_admin.initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# Streamlit UI configuration
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="centered")

# Sidebar for nickname
st.sidebar.title("Settings")
nickname = st.sidebar.text_input("Your AI companion's nickname:", value="CalmMate")

# Tabs: Chat, Journal, Mood Overview
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📓 Journal", "📊 Mood Overview"])

# ---------------- Chat Tab ----------------
with tab1:
    st.header(f"Chat with {nickname}")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat input
    user_input = st.text_input("You:", placeholder="Type here...")

    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = []
        db.reference("chat_history").set({})
        st.experimental_rerun()

    def detect_mood(text):
        prompt = f"""
        Determine the mood of this user message. Respond with only ONE of these words:
        Happy, Sad, Stressed, Anxious, Neutral, Excited

        Message: {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip()

    def save_to_firebase(ref_path, data):
        ref = db.reference(ref_path)
        ref.set(data)

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

        # Save to chat history
        chat_entry = {"user": user_input, "reply": reply, "mood": mood, "time": str(datetime.now())}
        st.session_state.chat_history.append(chat_entry)
        save_to_firebase("chat_history", st.session_state.chat_history)

    # Display chat
    for chat in st.session_state.chat_history:
        st.markdown(f"*You:* {chat['user']}")
        st.markdown(f"{nickname}:** {chat['reply']}")
        st.markdown(f"Detected Mood: {chat['mood']}")
        st.markdown("---")

# ---------------- Journal Tab ----------------
with tab2:
    st.header("📓 Journal / Reflection")

    if "journal_entries" not in st.session_state:
        st.session_state.journal_entries = []

    journal_input = st.text_area("Write your thoughts, feelings, or reflections here:")

    if st.button("💾 Save Reflection"):
        if journal_input.strip() != "":
            mood = detect_mood(journal_input)
            entry = {"text": journal_input, "mood": mood, "time": str(datetime.now())}
            st.session_state.journal_entries.append(entry)
            save_to_firebase("journal_entries", st.session_state.journal_entries)
            st.success("Reflection saved!")
        else:
            st.warning("Please write something before saving.")

    # Display journal entries
    if st.session_state.journal_entries:
        st.subheader("Your previous reflections")
        for entry in reversed(st.session_state.journal_entries):
            st.markdown(f"Time: {entry['time']}")
            st.markdown(f"Mood: {entry['mood']}")
            st.markdown(f"> {entry['text']}")
            st.markdown("---")

# ---------------- Mood Overview Tab ----------------
with tab3:
    st.header("📊 Mood & Trigger Overview")

    # Combine chat + journal moods
    all_moods = [c["mood"] for c in st.session_state.get("chat_history", [])] + \
                [j["mood"] for j in st.session_state.get("journal_entries", [])]

    if all_moods:
        mood_counts = pd.Series(all_moods).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No mood data yet. Start chatting or journaling!")
