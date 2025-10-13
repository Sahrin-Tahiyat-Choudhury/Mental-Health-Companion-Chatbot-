import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
firebase_url = os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# Streamlit UI configuration
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# Sidebar for AI nickname
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

st.sidebar.title("Settings")
st.session_state.nickname = st.sidebar.text_input(
    "Set AI nickname:", value=st.session_state.nickname
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Tabs for Chat and Mood Overview
tab_chat, tab_mood = st.tabs(["💬 Chat", "📊 Mood Overview"])

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

# ----- Chat Tab -----
with tab_chat:
    chat_container = st.container()

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type your message here...")
        submitted = st.form_submit_button("Send")
    
    if submitted and user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond in a gentle, neutral, supportive way.
        Do not offer medical advice. Keep it concise (2–3 sentences).

        User: {user_input}
        """
        with st.spinner("Thinking..."):
            reply = model.generate_content(prompt).text

        mood = detect_mood(user_input)
        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        save_to_firebase(st.session_state.history)

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Display chat dynamically
    for chat in st.session_state.history:
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")
        st.markdown(f"*You:* {chat['user']}")
        st.markdown(f"{st.session_state.nickname}:** {chat['reply']}")
        st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}")
        st.markdown("---")

# ----- Mood Overview Tab -----
with tab_mood:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.markdown("### Mood Overview")
        st.bar_chart(mood_counts, use_container_width=True)
    else:
        st.info("No mood data yet. Start chatting to see your mood trend!")

# Custom CSS for dark background and better visuals
st.markdown("""
<style>
body {
    background-color: #0E1117;
    color: #FFFFFF;
}
.stTextInput>div>div>input {
    background-color: #1A1C23;
    color: #FFFFFF;
}
.stButton>button {
    background-color: #2A2E3B;
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)
