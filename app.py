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
firebase_url = os.getenv("FIREBASE_DATABASE_URL")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase if not already initialized
if not hasattr(firebase_admin, "_apps") or not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_KEY_JSON"]))
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# Streamlit page config
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "reflections" not in st.session_state:
    st.session_state.reflections = []

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self Reflection"])

# ------------------- CHAT TAB -------------------
with tab1:
    # AI Nickname input
    if "ai_name" not in st.session_state:
        st.session_state.ai_name = "CalmMate"
    ai_name_input = st.text_input("AI Nickname:", value=st.session_state.ai_name)
    st.session_state.ai_name = ai_name_input.strip() or "CalmMate"

    # Chat section
    st.markdown("### Chat")
    chat_container = st.container()

    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type your message here...", key="chat_input")
        submitted = st.form_submit_button("Send")
        if submitted and user_input.strip():
            # AI response
            prompt = f"""
            You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
            Do not offer medical advice. Avoid inappropriate or unsafe topics. 
            Keep the message concise (2–3 sentences). 
            User: {user_input}
            """
            reply = model.generate_content(prompt).text

            # Mood detection
            mood_prompt = f"""
            Determine the mood of this user message. Respond with only ONE of these words: Happy, Sad, Stressed, Anxious, Neutral, Excited
            Message: {user_input}
            """
            mood = model.generate_content(mood_prompt).text.strip()

            # Save chat
            chat_entry = {"user": user_input, "reply": reply, "mood": mood}
            st.session_state.history.append(chat_entry)
            db.reference("chat_history").set(st.session_state.history)

    # Display chat above input
    with chat_container:
        for chat in st.session_state.history:
            user_html = f"""
            <div style='text-align: right; background-color: #1e1e1e; color: #fff; padding: 8px; border-radius: 8px; margin-bottom:5px'>
                <b>You:</b> {chat['user']}
            </div>
            """
            ai_html = f"""
            <div style='text-align: left; background-color: #2a2a2a; color: #fff; padding: 8px; border-radius: 8px; margin-bottom:5px'>
                <b>{st.session_state.ai_name}:</b> {chat['reply']}<br><i>Mood: {chat['mood']}</i>
            </div>
            """
            st.markdown(user_html, unsafe_allow_html=True)
            st.markdown(ai_html, unsafe_allow_html=True)

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.experimental_rerun = lambda: None  # dummy placeholder

# ------------------- MOOD OVERVIEW TAB -------------------
with tab2:
    st.markdown("### Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat history yet.")

# ------------------- SELF REFLECTION TAB -------------------
with tab3:
    st.markdown("### Self Reflection")
    # Reflection input form
    with st.form(key="reflection_form", clear_on_submit=True):
        reflection = st.text_area("Write your thoughts here:", key="reflection_box")
        reflection_submitted = st.form_submit_button("Save Reflection")
        if reflection_submitted and reflection.strip():
            st.session_state.reflections.append(reflection)
    
    # Display saved reflections
    for idx, r in enumerate(st.session_state.reflections):
        st.markdown(f"{idx+1}. {r}")
        if st.button(f"Delete {idx}", key=f"del_{idx}"):
            st.session_state.reflections.pop(idx)
            st.experimental_rerun = lambda: None  # dummy placeholder
