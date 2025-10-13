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
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
firebase_key_dict = st.secrets.get("FIREBASE_KEY_JSON")
firebase_url = st.secrets.get("FIREBASE_DB_URL") or os.getenv("FIREBASE_DB_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_key_dict))
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="centered")

# -------------------- Initialize Session --------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "cleared" not in st.session_state:
    st.session_state.cleared = False
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"  # default

# -------------------- Sidebar for Nickname --------------------
with st.sidebar:
    st.header("Customize AI Companion")
    nickname_input = st.text_input("Set AI nickname:", st.session_state.nickname)
    if nickname_input:
        st.session_state.nickname = nickname_input

# -------------------- Helper Functions --------------------
def generate_reply(user_input):
    prompt = f"""
    You are a calm, compassionate AI companion named {st.session_state.nickname}.
    Respond in a gentle, neutral, and supportive way.
    Do not offer medical advice or unsafe topics. Keep it concise (2–3 sentences).

    User: {user_input}
    """
    reply = model.generate_content(prompt).text

    mood_prompt = f"""
    Determine the mood of this user message. Respond with ONE word only:
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {user_input}
    """
    mood = model.generate_content(mood_prompt).text.strip()
    return reply, mood

def save_to_firebase(history):
    db.reference("chat_history").set(history)

# -------------------- Clear Chat --------------------
def clear_chat():
    st.session_state.history = []
    db.reference("chat_history").set({})
    st.session_state.cleared = True

# -------------------- Chat Section --------------------
st.title(f"💬 {st.session_state.nickname} – Your Supportive AI Companion")
st.markdown("Share how you're feeling today. Your messages appear above, and AI responds below.")

# Display chat history
for chat in st.session_state.history:
    st.markdown(f"<div style='background-color:#1f1f1f; color:white; padding:8px; border-radius:5px; margin-bottom:4px;'><b>You:</b> {chat['user']}</div>", unsafe_allow_html=True)
    mood_emoji = {
        "Happy": "😊",
        "Sad": "😢",
        "Stressed": "😟",
        "Anxious": "😰",
        "Neutral": "😐",
        "Excited": "😃"
    }.get(chat["mood"], "😐")
    st.markdown(f"<div style='background-color:#333333; color:#FFD700; padding:8px; border-radius:5px; margin-bottom:4px;'><b>{st.session_state.nickname}:</b> {chat['reply']} <i>(Mood: {chat['mood']} {mood_emoji})</i></div>", unsafe_allow_html=True)

# Clear chat button
if st.button("🗑 Clear Chat"):
    clear_chat()

if st.session_state.cleared:
    st.success("Chat cleared! Start a new conversation.")
    st.session_state.cleared = False

# Chat input
user_input = st.text_input("You:", placeholder="Type here...")

if user_input:
    reply, mood = generate_reply(user_input)
    chat_entry = {"user": user_input, "reply": reply, "mood": mood}
    st.session_state.history.append(chat_entry)
    save_to_firebase(st.session_state.history)

    # Display instantly
    st.markdown(f"<div style='background-color:#1f1f1f; color:white; padding:8px; border-radius:5px; margin-bottom:4px;'><b>You:</b> {user_input}</div>", unsafe_allow_html=True)
    mood_emoji = {
        "Happy": "😊",
        "Sad": "😢",
        "Stressed": "😟",
        "Anxious": "😰",
        "Neutral": "😐",
        "Excited": "😃"
    }.get(mood, "😐")
    st.markdown(f"<div style='background-color:#333333; color:#FFD700; padding:8px; border-radius:5px; margin-bottom:4px;'><b>{st.session_state.nickname}:</b> {reply} <i>(Mood: {mood} {mood_emoji})</i></div>", unsafe_allow_html=True)

# -------------------- Mood Overview --------------------
st.markdown("### 📊 Mood Overview")
if st.session_state.history:
    mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
    color_map = {
        "Happy": "#FFD700",      # gold
        "Sad": "#1E90FF",        # dodger blue
        "Stressed": "#FF4500",   # orange red
        "Anxious": "#8A2BE2",    # blue violet
        "Neutral": "#A9A9A9",    # dark grey
        "Excited": "#32CD32"     # lime green
    }
    chart_df = pd.DataFrame({"Count": mood_counts.values}, index=mood_counts.index)
    st.bar_chart(chart_df.style.set_properties({"color": "white", "background-color": chart_df.index.map(color_map)}))
else:
    st.info("No chat history yet. Start chatting to see mood trends!")
