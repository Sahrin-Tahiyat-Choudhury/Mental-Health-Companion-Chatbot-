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

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase safely
try:
    firebase_admin.get_app()
except ValueError:
    firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": st.secrets["FIREBASE_DATABASE_URL"]
    })

st.set_page_config(page_title="CalmMate - AI Companion", page_icon="💬", layout="wide")
st.title("💬 CalmMate – Your Supportive AI Companion")

# Tabs
tab1, tab2, tab3 = st.tabs(["Chat", "Mood Overview", "Self Reflection"])

# Nickname option
if "nickname" not in st.session_state:
    st.session_state.nickname = "CalmMate"
nickname_input = st.text_input("Set your AI nickname:", st.session_state.nickname)
if nickname_input:
    st.session_state.nickname = nickname_input

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "reflections" not in st.session_state:
    st.session_state.reflections = []

# --- Chat Tab ---
with tab1:
    # Placeholder for chat container
    chat_container = st.empty()

    # Clear chat button
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        db.reference("chat_history").set({})
        st.experimental_rerun()

    # Chat input using st.form for safe state updates
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type here...", key="chat_input")
        submitted = st.form_submit_button("Send")

    def detect_mood(text):
        prompt = f"""
        Determine the mood of this user message. Respond with only ONE of these words:   
        Happy, Sad, Stressed, Anxious, Neutral, Excited

        Message: {text}
        """
        response = model.generate_content(prompt)
        return response.text.strip()

    def save_to_firebase(chat_list):
        """Save entire session history to Firebase"""
        ref = db.reference("chat_history")
        ref.set(chat_list)

    if submitted and user_input:
        # Generate AI reply
        prompt = f"""
        You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
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

    # Render chat messages (scrollable)
    if st.session_state.history:
        chat_html = ""
        for chat in reversed(st.session_state.history):
            mood_emoji = {
                "Happy": "😊",
                "Sad": "😢",
                "Stressed": "😟",
                "Anxious": "😰",
                "Neutral": "😐",
                "Excited": "😃"
            }.get(chat["mood"], "😐")
            chat_html += f"""
            <div style='display:flex; flex-direction:column; margin-bottom:8px;'>
                <div style='align-self:flex-end; background-color:#2b2b2b; color:white; padding:8px; border-radius:10px; max-width:70%;'>
                    <b>You:</b> {chat['user']}
                </div>
                <div style='align-self:flex-start; background-color:#1f1f1f; color:#a8dadc; padding:8px; border-radius:10px; max-width:70%; margin-top:3px;'>
                    <b>{st.session_state.nickname}:</b> {chat['reply']}<br><i>Mood:</i> {chat['mood']} {mood_emoji}
                </div>
            </div>
            """
        chat_container.markdown(f"<div style='max-height:500px; overflow-y:auto;'>{chat_html}</div>", unsafe_allow_html=True)

# --- Mood Overview Tab ---
with tab2:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat history yet to generate mood chart.")

# --- Self Reflection Tab ---
with tab3:
    # Reflection input form
    with st.form(key="reflection_form", clear_on_submit=True):
        reflection_input = st.text_area("Write your reflection here:", key="reflection_box")
        submitted_reflection = st.form_submit_button("💾 Save Reflection")
    if submitted_reflection and reflection_input.strip():
        st.session_state.reflections.append(reflection_input)
        st.experimental_rerun()

    # Display saved reflections with delete option
    if st.session_state.reflections:
        st.markdown("### Saved Reflections")
        for i, ref in enumerate(st.session_state.reflections):
            col1, col2 = st.columns([9,1])
            with col1:
                st.markdown(f"{i+1}. {ref}")
            with col2:
                if st.button(f"🗑", key=f"delete_ref_{i}"):
                    st.session_state.reflections.pop(i)
                    st.experimental_rerun()
