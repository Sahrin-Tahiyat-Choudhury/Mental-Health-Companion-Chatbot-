import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# ---------- Load Environment / Secrets ----------
load_dotenv()
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
firebase_key_json = st.secrets.get("FIREBASE_KEY_JSON") or os.getenv("FIREBASE_KEY_JSON")
firebase_url = st.secrets.get("FIREBASE_DB_URL") or os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    firebase_key_dict = json.loads(firebase_key_json)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="centered")

# Sidebar: nickname input
with st.sidebar:
    st.header("Settings")
    companion_name = st.text_input("AI Companion Nickname:", value="CalmMate")

# Tabs
chat_tab, mood_tab = st.tabs(["💬 Chat", "📊 Mood Overview"])

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Chat Tab ----------
with chat_tab:
    st.markdown(f"### Chat with {companion_name}")

    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message:", placeholder="Type here...")
        submitted = st.form_submit_button("Send")

        if submitted and user_input.strip():
            # Generate AI reply
            prompt = f"""
            You are a calm, compassionate AI companion named {companion_name}. 
            Respond gently, neutrally, and supportively.
            Do not give medical advice. Avoid unsafe topics.
            Keep reply concise (2–3 sentences).

            User: {user_input}
            """
            reply = model.generate_content(prompt).text  # fixed NoneType error

            # Detect mood
            mood_prompt = f"""
            Determine the mood of this message. Respond with only one of:
            Happy, Sad, Stressed, Anxious, Neutral, Excited.

            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            # Add to session history
            chat_entry = {"user": user_input, "reply": reply, "mood": mood}
            st.session_state.history.append(chat_entry)

            # Save to Firebase
            ref = db.reference("chat_history")
            ref.set(st.session_state.history)

    # Display chat history
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
        st.markdown(f"{companion_name}: {chat['reply']}")
        st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}")
        st.markdown("---")

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared! Start a new conversation.")

# ---------- Mood Overview Tab ----------
with mood_tab:
    st.markdown("### Your Mood History")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No mood history yet. Chat with your companion to see mood trends.")
