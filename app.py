import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# -----------------------
# Load environment variables
# -----------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_url = os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not hasattr(firebase_admin, "_apps") or not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_KEY_JSON"]))
    firebase_admin.initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="centered")

# Tabs
tab1, tab2 = st.tabs(["💬 Chat", "📊 Mood Overview"])

# Session state
if "history" not in st.session_state:
    st.session_state.history = []

if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

# -----------------------
# Chat Tab
# -----------------------
with tab1:
    st.markdown("### Customize AI Name")
    st.session_state.nickname = st.text_input("Your AI companion's nickname:", st.session_state.nickname)

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Chat input
    user_input = st.text_input("You:", placeholder="Type here...", key="chat_input")

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

    if user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
        Do not offer medical advice. Avoid inappropriate or unsafe topics. 
        Keep the message concise (2–3 sentences). 

        User: {user_input}
        """
        with st.spinner("Thinking..."):
            reply = model.generate_content(prompt).text.strip()

        # Generate reflection/suggestion
        reflection_prompt = f"""
        You are a calm AI companion. Give a short, safe, practical reflection or coping suggestion 
        for the user based on their message: {user_input}.
        Avoid anything haram or religious-specific.
        """
        reflection = model.generate_content(reflection_prompt).text.strip()

        mood = detect_mood(user_input)

        # Add to session history
        chat_entry = {"user": user_input, "reply": reply, "mood": mood, "reflection": reflection}
        st.session_state.history.append(chat_entry)
        save_to_firebase(st.session_state.history)

    # Display chat
    st.markdown("<div style='max-height:500px; overflow-y:auto;'>", unsafe_allow_html=True)
    for chat in st.session_state.history:
        # Mood emoji
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")

        # User message
        st.markdown(f"<div style='text-align:right; color:#ffffff; background-color:#444; padding:8px; border-radius:8px; margin-bottom:4px;'>You: {chat['user']}</div>", unsafe_allow_html=True)
        
        # AI message
        st.markdown(f"<div style='text-align:left; color:#ffffff; background-color:#1f1f1f; padding:8px; border-radius:8px; margin-bottom:4px;'>{st.session_state.nickname}: {chat['reply']}<br><small>Reflection: {chat['reflection']}</small></div>", unsafe_allow_html=True)
        
        # Mood
        st.markdown(f"<div style='font-size:0.9em; color:#bbb; margin-bottom:8px;'>Detected Mood: {chat['mood']} {mood_emoji}</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Mood Overview Tab
# -----------------------
with tab2:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat history yet. Start a conversation to see mood trends.")
