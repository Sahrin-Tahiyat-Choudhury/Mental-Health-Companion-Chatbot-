import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from firebase_admin import credentials, db, initialize_app

# -------------------------
# Streamlit page settings
# -------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# -------------------------
# User nickname
# -------------------------
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

nickname_input = st.text_input("Give your AI companion a nickname:", value=st.session_state.nickname)
if nickname_input:
    st.session_state.nickname = nickname_input

# -------------------------
# Configure Gemini
# -------------------------
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# -------------------------
# Initialize Firebase safely
# -------------------------
if not len(db._apps):
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_KEY_JSON"]))
    initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# -------------------------
# Initialize session state
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# Tabs for Chat and Mood
# -------------------------
tab1, tab2 = st.tabs(["💬 Chat", "📊 Mood Overview"])

with tab1:
    # Chat display
    chat_container = st.container()

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.success("Chat cleared!")

    # Chat input
    user_input = st.text_input("You:", placeholder="Type here...")

    # Functions
    def detect_mood(text):
        prompt = f"""
        Determine the mood of this user message. Respond with only ONE of these words: 
        Happy, Sad, Stressed, Anxious, Neutral, Excited
        Message: {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip()

    def save_to_firebase(chat_list):
        db.reference("chat_history").set(chat_list)

    if user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond in a gentle, supportive way.
        Do not offer medical advice or inappropriate content.
        Keep it concise (2–3 sentences).
        Avoid haram suggestions.
        User: {user_input}
        """
        with st.spinner("Thinking..."):
            reply = model.generate_content(prompt).text

        mood = detect_mood(user_input)

        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        save_to_firebase(st.session_state.history)

    # Display chat history in ChatGPT style
    for chat in st.session_state.history:
        col1, col2 = st.columns([1, 4])
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")

        # User message on right
        with col2:
            st.markdown(
                f"<div style='background-color:#1f1f1f; padding:10px; border-radius:8px; text-align:right;'>*You:* {chat['user']}</div>",
                unsafe_allow_html=True,
            )

        # AI message on left
        with col1:
            st.markdown(
                f"<div style='background-color:#2b2b2b; padding:10px; border-radius:8px;'>{st.session_state.nickname}:** {chat['reply']}</div>",
                unsafe_allow_html=True,
            )
        st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}")
        st.markdown("---")

with tab2:
    # Mood overview
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No mood data yet. Start chatting to see mood trends!")
