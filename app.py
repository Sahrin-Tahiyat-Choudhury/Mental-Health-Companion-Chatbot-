import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime

# ------------------------
# Load secrets
# ------------------------
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
firebase_url = st.secrets["FIREBASE_DATABASE_URL"]

# ------------------------
# Configure Gemini
# ------------------------
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# ------------------------
# Initialize Firebase
# ------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# ------------------------
# Streamlit UI
# ------------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="wide")

# ------------------------
# Initialize session state
# ------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# ------------------------
# Tabs
# ------------------------
tabs = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self-Reflection"])

# ------------------------
# Chat Tab
# ------------------------
with tabs[0]:
    st.header(f"Chat with {st.session_state.nickname}")
    
    # Chat display container
    chat_container = st.container()
    
    # Chat input
    st.session_state.user_input = st.text_input(
        "You:", value=st.session_state.user_input, placeholder="Type your message here..."
    )
    
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        chat_container.empty()
    
    # Process user input
    if st.session_state.user_input:
        user_msg = st.session_state.user_input
        # Generate CalmMate reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
        Do not offer medical advice. Avoid inappropriate or unsafe topics.
        Keep the message concise (2–3 sentences).
        User: {user_msg}
        """
        with st.spinner("Thinking..."):
            reply = model.generate_content(prompt).text
        
        # Detect mood
        mood_prompt = f"""
        Determine the mood of this user message. Respond with only ONE of these words:
        Happy, Sad, Stressed, Anxious, Neutral, Excited
        Message: {user_msg}
        """
        mood = model.generate_content(mood_prompt).text.strip()
        
        # Add to history
        chat_entry = {"user": user_msg, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        db.reference("chat_history").set(st.session_state.history)
        
        # Clear input
        st.session_state.user_input = ""
    
    # Display chat history (above input)
    for chat in reversed(st.session_state.history):
        # AI message (left)
        st.markdown(
            f"<div style='background-color:#2f2f2f; color:white; padding:10px; border-radius:10px; width:70%; margin-bottom:5px'>{st.session_state.nickname}: {chat['reply']}</div>",
            unsafe_allow_html=True
        )
        # User message (right)
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

# ------------------------
# Mood Overview Tab
# ------------------------
with tabs[1]:
    st.header("Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat data yet to display mood overview.")

# ------------------------
# Self-Reflection Tab
# ------------------------
with tabs[2]:
    st.header("Self Reflection")
    reflection_text = st.text_area("Write your thoughts here...")
    
    if st.button("💾 Save Reflection"):
        if reflection_text.strip():
            entry = {"text": reflection_text.strip(), "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            st.session_state.journal_entries.append(entry)
            db.reference("journal_entries").set(st.session_state.journal_entries)
            st.success("Reflection saved!")
    
    # Reflection display container
    reflection_container = st.container()
    with reflection_container:
        for idx, entry in enumerate(reversed(st.session_state.journal_entries)):
            st.markdown(f"Time: {entry['time']}")
            st.markdown(f"> {entry['text']}")
            if st.button(f"🗑 Delete Entry {idx}", key=f"del{idx}"):
                real_idx = len(st.session_state.journal_entries) - 1 - idx
                st.session_state.journal_entries.pop(real_idx)
                db.reference("journal_entries").set(st.session_state.journal_entries)
                reflection_container.empty()
                break
