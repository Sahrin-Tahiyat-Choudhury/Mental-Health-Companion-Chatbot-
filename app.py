import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# -------------------- Load Secrets --------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_url = os.getenv("FIREBASE_DB_URL")
firebase_key_json = st.secrets["FIREBASE_KEY_JSON"]

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    firebase_key_dict = json.loads(firebase_key_json)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# -------------------- Streamlit Setup --------------------
st.set_page_config(page_title="Mental Health Companion", layout="wide")
st.title("💬 Mental Health Companion")

# -------------------- Tabs --------------------
tabs = st.tabs(["Chat", "Mood Overview"])

# -------------------- Session State --------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

# -------------------- Helper Functions --------------------
def detect_mood(text):
    prompt = f"""
    Determine the mood of this user message. Respond with only ONE of these words: 
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def save_to_firebase(chat_list):
    ref = db.reference("chat_history")
    ref.set(chat_list)

def mood_emoji(mood):
    return {
        "Happy": "😊",
        "Sad": "😢",
        "Stressed": "😟",
        "Anxious": "😰",
        "Neutral": "😐",
        "Excited": "😃"
    }.get(mood, "😐")

# -------------------- Chat Tab --------------------
with tabs[0]:
    st.subheader("💬 Chat with your AI Companion")
    
    # Nickname input
    nickname_input = st.text_input("AI Nickname:", value=st.session_state.nickname)
    st.session_state.nickname = nickname_input if nickname_input.strip() else "CalmMate"

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        save_to_firebase([])
        st.success("Chat cleared!")

    # Display chat history
    for chat in st.session_state.history:
        # AI bubble
        st.markdown(f"""
        <div style='background-color:#2C2F33; padding:10px; border-radius:10px; margin-bottom:5px; width:65%;'>
        <b>{st.session_state.nickname}:</b> {chat['reply']} <br>
        <small>Mood: {chat['mood']} {mood_emoji(chat['mood'])}</small>
        </div>
        """, unsafe_allow_html=True)
        # User bubble
        st.markdown(f"""
        <div style='background-color:#7289DA; color:white; padding:10px; border-radius:10px; margin-bottom:10px; width:65%; margin-left:auto;'>
        <b>You:</b> {chat['user']}
        </div>
        """, unsafe_allow_html=True)

    # Chat input form at bottom
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message:", placeholder="Type here...")
        submitted = st.form_submit_button("Send")

        if submitted and user_input.strip():
            # AI reply
            prompt = f"""
            You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
            Do not offer medical advice. Avoid inappropriate or unsafe topics.
            Keep the message concise (2–3 sentences).

            User: {user_input}
            """
            reply = model.generate_content(prompt).text
            mood = detect_mood(user_input)

            chat_entry = {"user": user_input, "reply": reply, "mood": mood}
            st.session_state.history.append(chat_entry)
            save_to_firebase(st.session_state.history)
            st.experimental_rerun()

# -------------------- Mood Overview Tab --------------------
with tabs[1]:
    st.subheader("📊 Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat yet to display mood overview.")
