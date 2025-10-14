import streamlit as st
import google.generativeai as genai
import json
from firebase_admin import credentials, db, initialize_app
import firebase_admin

# ---------- SETUP SECRETS ----------
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

if not firebase_admin._apps:
    firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(firebase_key_dict)
    initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# ---------- TABS ----------
tabs = st.tabs(["💬 Chat", "📝 Self Reflection", "⚙ Settings"])

# ---------- SETTINGS TAB ----------
with tabs[2]:
    st.header("Settings")
    nickname_input = st.text_input("AI Nickname:", st.session_state.nickname)
    if nickname_input:
        st.session_state.nickname = nickname_input

# ---------- CHAT TAB ----------
with tabs[0]:
    st.header(f"Chat with {st.session_state.nickname}")

    # Display chat history container (scrollable)
    chat_container = st.container()
    for chat in reversed(st.session_state.get("history", [])):
        # AI reply
        st.markdown(
            f"<div style='background-color:#2f2f2f; color:white; padding:10px; border-radius:10px; width:70%; margin-bottom:5px'>{st.session_state.nickname}: {chat['reply']}</div>",
            unsafe_allow_html=True
        )
        # User message
        st.markdown(
            f"<div style='background-color:#0a9396; color:white; padding:10px; border-radius:10px; width:70%; margin-left:30%; margin-bottom:5px'>You: {chat['user']}</div>",
            unsafe_allow_html=True
        )
        # Mood
        mood_emoji = {
            "Happy": "😊",
            "Sad": "😢",
            "Stressed": "😟",
            "Anxious": "😰",
            "Neutral": "😐",
            "Excited": "😃"
        }.get(chat["mood"], "😐")
        st.markdown(f"Detected Mood: {chat['mood']} {mood_emoji}")
        st.markdown("---")

    # Chat input
    if "input_box" not in st.session_state:
        st.session_state.input_box = ""
    user_input = st.text_input("You:", key="input_box", placeholder="Type your message here...")

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        chat_container.empty()

    if user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
        Do not offer medical advice. Avoid inappropriate or unsafe topics.
        Keep the message concise (2–3 sentences).
        User: {user_input}
        """
        reply = model.generate_content(prompt).text

        # Detect mood
        mood_prompt = f"""
        Determine the mood of this user message. Respond with only ONE of these words:
        Happy, Sad, Stressed, Anxious, Neutral, Excited
        Message: {user_input}
        """
        mood = model.generate_content(mood_prompt).text.strip()

        # Save chat
        if "history" not in st.session_state:
            st.session_state.history = []
        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        db.reference("chat_history").set(st.session_state.history)

        # Clear input box
        st.session_state.input_box = ""

# ---------- SELF REFLECTION TAB ----------
with tabs[1]:
    st.header("Self Reflection")
    if "reflection" not in st.session_state:
        st.session_state.reflection = []

    reflection_input = st.text_area("Write your thoughts here:")
    if st.button("💾 Save Entry"):
        if reflection_input.strip():
            st.session_state.reflection.append(reflection_input.strip())
            st.success("Saved!")
            st.experimental_rerun()

    # Show saved reflections
    for i, entry in enumerate(st.session_state.reflection):
        st.markdown(f"*Entry {i+1}:* {entry}")
        if st.button(f"🗑 Delete Entry {i+1}", key=f"del_{i}"):
            st.session_state.reflection.pop(i)
            st.experimental_rerun()
