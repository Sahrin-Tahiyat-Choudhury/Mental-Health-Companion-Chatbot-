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

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# -----------------------
# Initialize Firebase
# -----------------------
if not firebase_admin._apps:
    firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": st.secrets["FIREBASE_DATABASE_URL"]
    })

# -----------------------
# Streamlit page config
# -----------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# -----------------------
# Initialize session state
# -----------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "reflections" not in st.session_state:
    st.session_state.reflections = []

if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

# -----------------------
# Helper functions
# -----------------------
def detect_mood(text):
    prompt = f"""
    Determine the mood of this user message. Respond with only ONE of these words:
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {text}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def save_to_firebase(chat_list, reflection_list=None):
    """Save entire session history to Firebase"""
    db.reference("chat_history").set(chat_list)
    if reflection_list is not None:
        db.reference("reflections").set(reflection_list)

# -----------------------
# Tabs
# -----------------------
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self Reflection"])

# -----------------------
# Tab 1: Chat
# -----------------------
with tab1:
    st.subheader("Chat with your AI Companion")

    # Nickname input
    nickname_input = st.text_input("Set AI Nickname:", value=st.session_state.nickname)
    st.session_state.nickname = nickname_input if nickname_input else "CalmMate"

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        save_to_firebase([])
        st.experimental_rerun()

    # Display chat (above input)
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.history:
            st.markdown(
                f"<div style='background-color:#2f2f2f;color:white;padding:8px;border-radius:10px;width:70%;margin-bottom:5px;'>"
                f"{st.session_state.nickname}:** {chat['reply']}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='background-color:#1f4e78;color:white;padding:8px;border-radius:10px;width:70%;margin-left:30%;margin-bottom:5px;'>"
                f"*You:* {chat['user']}</div>",
                unsafe_allow_html=True
            )

    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type your message here...", key="input_box")
        submitted = st.form_submit_button("Send")
        if submitted and user_input:
            prompt = f"""
            You are a calm, compassionate AI companion named {st.session_state.nickname}.
            Respond in a gentle, supportive way, concise 2-3 sentences. Avoid any haram suggestions.
            User: {user_input}
            """
            reply = model.generate_content(prompt).text
            mood = detect_mood(user_input)
            chat_entry = {"user": user_input, "reply": reply, "mood": mood}
            st.session_state.history.append(chat_entry)
            save_to_firebase(st.session_state.history)
            st.experimental_rerun()

# -----------------------
# Tab 2: Mood Overview
# -----------------------
with tab2:
    st.subheader("Your Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat data yet to show mood overview.")

# -----------------------
# Tab 3: Self Reflection
# -----------------------
with tab3:
    st.subheader("Self Reflection")

    # Reflection input form
    with st.form("reflection_form", clear_on_submit=True):
        reflection_text = st.text_area("Write your thoughts here...", key="reflection_box")
        submitted_reflection = st.form_submit_button("Save Reflection")
        if submitted_reflection and reflection_text:
            reflection_entry = {"text": reflection_text, "mood": detect_mood(reflection_text)}
            st.session_state.reflections.append(reflection_entry)
            save_to_firebase(st.session_state.history, st.session_state.reflections)
            st.success("Reflection saved!")

    # Display saved reflections
    for idx, ref in enumerate(st.session_state.reflections):
        st.markdown(
            f"<div style='background-color:#3a3a3a;color:white;padding:8px;border-radius:10px;margin-bottom:5px;'>"
            f"{ref['text']}</div>",
            unsafe_allow_html=True
        )
        if st.button(f"Delete Entry {idx}"):
            st.session_state.reflections.pop(idx)
            save_to_firebase(st.session_state.history, st.session_state.reflections)
            st.experimental_rerun()
