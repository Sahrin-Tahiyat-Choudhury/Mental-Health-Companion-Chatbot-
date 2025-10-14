import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

# Load environment variables if needed
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase safely
try:
    firebase_admin.get_app()
except ValueError:
    firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# Streamlit UI
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# Sidebar - nickname
st.sidebar.title("Settings")
nickname = st.sidebar.text_input("Choose your chatbot nickname:", value="CalmMate")

# Tabs
tab1, tab2 = st.tabs(["Chat", "Mood Overview"])

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "cleared" not in st.session_state:
    st.session_state.cleared = False

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

with tab1:
    # Chat input
    user_input = st.text_input("You:", placeholder="Type your message here...", key="user_input")

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        save_to_firebase(st.session_state.history)
        st.session_state.cleared = True

    if st.session_state.cleared:
        st.success("Chat cleared! Start a new conversation.")
        st.session_state.cleared = False

    if user_input:
        prompt = f"""
        You are a calm, compassionate AI companion named {nickname}. 
        Respond to the user in a gentle, neutral, and supportive way.
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

    # Display chat history with dark colors, like ChatGPT
    if st.session_state.history:
        st.markdown(
            """
            <style>
            .user-msg {background-color:#2E3440; color:white; padding:10px; border-radius:10px; text-align:right;}
            .ai-msg {background-color:#3B4252; color:white; padding:10px; border-radius:10px; text-align:left;}
            .chat-box {max-height:500px; overflow-y:auto; padding:10px;}
            </style>
            """, unsafe_allow_html=True
        )
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for chat in st.session_state.history:
            mood_emoji = {
                "Happy": "😊",
                "Sad": "😢",
                "Stressed": "😟",
                "Anxious": "😰",
                "Neutral": "😐",
                "Excited": "😃"
            }.get(chat["mood"], "😐")
            st.markdown(f'<div class="user-msg">You: {chat["user"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-msg">{nickname}: {chat["reply"]}</div>', unsafe_allow_html=True)
            st.markdown(f'Detected Mood: {chat["mood"]} {mood_emoji}', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    # Mood Overview
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.write("No moods to display yet. Start chatting!")
