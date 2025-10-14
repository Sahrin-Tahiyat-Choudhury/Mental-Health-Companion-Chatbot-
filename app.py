import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import pandas as pd
import plotly.graph_objects as go
import firebase_admin
from firebase_admin import credentials, db

# -----------------------------
# Load secrets and configure APIs
# -----------------------------
load_dotenv()
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
firebase_url = st.secrets["FIREBASE_DATABASE_URL"]

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

# -----------------------------
# Session state initialization
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "reflections" not in st.session_state:
    st.session_state.reflections = []

if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

# -----------------------------
# Tabs
# -----------------------------
tabs = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self-Reflection"])

# -----------------------------
# Chat Tab
# -----------------------------
with tabs[0]:
    st.subheader("Chat")
    nickname_input = st.text_input("Choose a nickname for the AI:", st.session_state.nickname)
    st.session_state.nickname = nickname_input or st.session_state.nickname

    chat_container = st.container()

    user_input = st.text_input("Type your message here...", key="input_box")
    send_btn = st.button("Send")

    if send_btn and user_input.strip():
        # Generate AI response
        prompt = f"""
        You are a calm, compassionate AI companion named {st.session_state.nickname}. 
        Respond to the user in a gentle, neutral, and supportive way.
        Do not offer medical advice or inappropriate content.
        User: {user_input}
        """
        with st.spinner("Thinking..."):
            reply = model.generate_content(prompt).text

        # Detect mood
        mood_prompt = f"""
        Determine the mood of this user message. Respond with only ONE word:
        Happy, Sad, Stressed, Anxious, Neutral, Excited
        Message: {user_input}
        """
        mood = model.generate_content(mood_prompt).text.strip()

        entry = {"user": user_input, "ai": reply, "mood": mood}
        st.session_state.chat_history.append(entry)
        db.reference("chat_history").set(st.session_state.chat_history)

        st.session_state.input_box = ""  # Clear input

    # Display chat (ChatGPT style)
    for chat in st.session_state.chat_history:
        st.markdown(f"<div style='text-align:right; background-color:#1F1F1F; color:white; padding:8px; border-radius:8px; margin-bottom:5px;'>{chat['user']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:left; background-color:#333333; color:white; padding:8px; border-radius:8px; margin-bottom:10px;'>{st.session_state.nickname}: {chat['ai']}</div>", unsafe_allow_html=True)

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        db.reference("chat_history").set({})
        st.experimental_rerun()

# -----------------------------
# Mood Overview Tab
# -----------------------------
with tabs[1]:
    st.subheader("Mood Overview")

    all_moods = ["Happy", "Sad", "Stressed", "Anxious", "Neutral", "Excited"]
    mood_colors = {
        "Happy": "#FFD700", "Sad": "#1E90FF", "Stressed": "#FF4500",
        "Anxious": "#FF69B4", "Neutral": "#808080", "Excited": "#32CD32"
    }

    mood_counts = pd.Series([c["mood"] for c in st.session_state.chat_history]).value_counts()
    mood_counts = mood_counts.reindex(all_moods, fill_value=0)

    fig = go.Figure(
        data=[go.Bar(
            x=all_moods,
            y=[mood_counts[m] for m in all_moods],
            marker_color=[mood_colors[m] for m in all_moods],
            text=[mood_counts[m] for m in all_moods],
            textposition='auto'
        )]
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Self-Reflection Tab
# -----------------------------
with tabs[2]:
    st.subheader("Self-Reflection")

    reflection_input = st.text_area("Write your reflection here...", key="reflection_box")
    save_btn = st.button("Save Reflection")

    if save_btn and reflection_input.strip():
        mood_prompt = f"""
        Determine the mood of this reflection. Respond with only ONE word:
        Happy, Sad, Stressed, Anxious, Neutral, Excited
        Message: {reflection_input}
        """
        mood = model.generate_content(mood_prompt).text.strip()
        st.session_state.reflections.append({"text": reflection_input, "mood": mood})
        reflection_input = ""  # Clear after saving

    if st.session_state.reflections:
        st.markdown("### Saved Reflections")
        for i, r in enumerate(st.session_state.reflections):
            st.markdown(f"- {r['text']} ({r['mood']})")
            if st.button(f"Delete {i}"):
                st.session_state.reflections.pop(i)
                st.experimental_rerun()
