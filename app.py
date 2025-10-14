import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from firebase_admin import credentials, initialize_app, db
import firebase_admin

# ------------------- INITIAL SETUP -------------------
st.set_page_config(page_title="Mental Health Companion", page_icon="💬", layout="centered")

# Load secrets
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
firebase_db_url = st.secrets["FIREBASE_DATABASE_URL"]

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    initialize_app(cred, {"databaseURL": firebase_db_url})

# ------------------- SESSION STATE -------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"

if "reflections" not in st.session_state:
    st.session_state.reflections = []

if "input_box" not in st.session_state:
    st.session_state.input_box = ""

if "reflection_box" not in st.session_state:
    st.session_state.reflection_box = ""

# ------------------- HELPERS -------------------
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

def save_reflection_to_firebase(reflections):
    ref = db.reference("reflections")
    ref.set(reflections)

# ------------------- TABS -------------------
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self Reflection"])

# ------------------- CHAT TAB -------------------
with tab1:
    st.subheader("Chat with your AI Companion")
    
    # Nickname input
    nickname = st.text_input("Set AI Nickname:", value=st.session_state.nickname)
    st.session_state.nickname = nickname if nickname else "CalmMate"

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        save_to_firebase([])
        st.experimental_rerun()

    # Chat input (always at bottom)
    user_input = st.text_input("You:", value=st.session_state.input_box, key="input_box", placeholder="Type your message here...")
    
    if user_input:
        prompt = f"""
        You are a calm, compassionate AI companion named {st.session_state.nickname}.
        Respond in a gentle, supportive way, concise 2-3 sentences. Do not give medical advice.
        User: {user_input}
        """
        reply = model.generate_content(prompt).text
        mood = detect_mood(user_input)
        
        chat_entry = {"user": user_input, "reply": reply, "mood": mood}
        st.session_state.history.append(chat_entry)
        save_to_firebase(st.session_state.history)
        
        # Reset input
        st.session_state.input_box = ""
        st.experimental_rerun()

    # Display chat above input
    for chat in st.session_state.history:
        st.markdown(f"<div style='background-color:#2f2f2f;color:white;padding:8px;border-radius:10px;width:70%;margin-bottom:5px;'>{st.session_state.nickname}:** {chat['reply']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color:#1f4e78;color:white;padding:8px;border-radius:10px;width:70%;margin-left:30%;margin-bottom:5px;'>*You:* {chat['user']}</div>", unsafe_allow_html=True)

# ------------------- MOOD OVERVIEW TAB -------------------
with tab2:
    st.subheader("Mood Overview")
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat history to display mood yet.")

# ------------------- SELF REFLECTION TAB -------------------
with tab3:
    st.subheader("Self Reflection")
    reflection_text = st.text_area("Write your thoughts here:", value=st.session_state.reflection_box, key="reflection_box")
    if st.button("💾 Save Reflection"):
        if reflection_text.strip():
            st.session_state.reflections.append({"text": reflection_text})
            save_reflection_to_firebase(st.session_state.reflections)
            st.session_state.reflection_box = ""
            st.experimental_rerun()
    
    if st.session_state.reflections:
        st.markdown("### Saved Reflections")
        for idx, ref in enumerate(st.session_state.reflections.copy()):
            st.write(ref["text"])
            delete_key = f"del_{idx}"
            if st.button("🗑 Delete", key=delete_key):
                st.session_state.reflections.pop(idx)
                save_reflection_to_firebase(st.session_state.reflections)
                st.experimental_rerun()
