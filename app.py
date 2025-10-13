import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# ---------- Configuration ----------

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
firebase_url = os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    firebase_key_dict = json.loads(firebase_key_json)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# ---------- Streamlit UI ----------

st.set_page_config(page_title="CalmMate - AI Companion", page_icon="💬", layout="centered")
st.title("💬 CalmMate – Your Supportive AI Companion")
st.markdown("Share how you're feeling today. CalmMate will reply with empathy and care.")

# Initialize session state properly
if "history" not in st.session_state or st.session_state.history is None:
    st.session_state.history = []

# Clear chat button
if st.button("🗑 Clear Chat"):
    st.session_state.history = []
    db.reference("chat_history").set({})
    st.success("Chat cleared! Start a new conversation.")

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
        reply_obj = model.generate_content(prompt)
        reply = reply_obj.text if reply_obj else "Sorry, I couldn't generate a response."

    mood = detect_mood(user_input)

    # Add to session history
    chat_entry = {"user": user_input, "reply": reply, "mood": mood}
    st.session_state.history.append(chat_entry)
    save_to_firebase(st.session_state.history)

# Display chat history
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

    # Mood trend chart
    mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
    st.bar_chart(mood_counts)
