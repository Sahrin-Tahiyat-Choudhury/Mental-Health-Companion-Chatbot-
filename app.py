import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# --- CHANGE #1: Use st.secrets instead of dotenv ---
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_url = st.secrets["FIREBASE_DB_URL"]

firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    # firebase_key.json should be uploaded to your repo or added in secrets as string
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": firebase_url
    })

# Streamlit UI
st.set_page_config(page_title="CalmMate - AI Companion", page_icon="💬", layout="centered")
st.title("💬 CalmMate – Your Supportive AI Companion")
st.markdown("Share how you're feeling today. CalmMate will reply with empathy and care.")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Clear chat button
if st.button("🗑 Clear Chat"):
    st.session_state.history = []
    db.reference("chat_history").set({})
    st.session_state.cleared = True

if "cleared" in st.session_state and st.session_state.cleared:
    st.success("Chat cleared! Start a new conversation.")
    st.session_state.cleared = False

# Chat input
user_input = st.text_input("You:", placeholder="Type here...")

def detect_mood(text):
    prompt = f"""
    Determine the mood of this user message. Respond with only ONE of these words:
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def save_to_firebase(chat_list):
    """Save entire session history to Firebase"""
    ref = db.reference("chat_history")
    ref.set(chat_list)

if user_input:
    # Generate CalmMate reply
    prompt = f"""
    You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
    Do not offer medical advice. Avoid inappropriate or unsafe topics.
    Keep the message concise (2–3 sentences).

    User: {user_input}
    """
    with st.spinner("Thinking..."):
        reply = model.generate_content(prompt).text

    mood = detect_mood(user_input)

    chat_entry = {"user": user_input, "reply": reply, "mood": mood}
    st.session_state.history.append(chat_entry)
    save_to_firebase(st.session_state.history)

if st.session_state.history:
    st.markdown("### 💬 Chat History")
    for chat in st.session_state.history:
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")
        st.markdown(f"You: {chat['user']}")
        st.markdown(f"CalmMate: {chat['reply']}")
        st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}")
        st.markdown("---")

    mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
    st.bar_chart(mood_counts)

