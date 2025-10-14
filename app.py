import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db

# -----------------------
# Streamlit page config
# -----------------------
st.set_page_config(
    page_title="Mental Health Companion",
    page_icon="💬",
    layout="wide"
)

# -----------------------
# Load secrets
# -----------------------
api_key = st.secrets["GOOGLE_API_KEY"]
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
firebase_url = st.secrets["FIREBASE_DATABASE_URL"]

# -----------------------
# Configure Gemini
# -----------------------
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# -----------------------
# Initialize Firebase
# -----------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})

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
# Tabs
# -----------------------
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Self-Reflection"])

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

def save_to_firebase(data, ref_name):
    ref = db.reference(ref_name)
    ref.set(data)

# -----------------------
# Chat Tab
# -----------------------
with tab1:
    # Nickname input
    nickname_input = st.text_input("Set AI nickname:", st.session_state.nickname)
    if nickname_input:
        st.session_state.nickname = nickname_input.strip()

    # Chat display container
    chat_container = st.container()
    with chat_container:
        if st.session_state.history:
            for chat in st.session_state.history:
                user_col, ai_col = st.columns([3,7])
                with user_col:
                    st.markdown(f"<div style='text-align:right;color:#ffffff;background-color:#1f2937;padding:5px;border-radius:5px'>{chat['user']}</div>", unsafe_allow_html=True)
                with ai_col:
                    st.markdown(f"<div style='text-align:left;color:#ffffff;background-color:#374151;padding:5px;border-radius:5px'>{st.session_state.nickname}: {chat['reply']}</div>", unsafe_allow_html=True)
                st.markdown("---")

    # Clear chat
    if st.button("🗑 Clear Chat"):
        st.session_state.history = []
        save_to_firebase([], "chat_history")

    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Type your message here...", key="chat_input")
        submitted = st.form_submit_button("Send")
        if submitted and user_input.strip():
            # AI reply
            prompt = f"""
            You are a calm, compassionate AI companion. Respond to the user in a gentle, neutral, and supportive way.
            Do not offer medical advice. Avoid inappropriate or unsafe topics. 
            Keep the message concise (2–3 sentences). 
            User: {user_input}
            """
            reply = model.generate_content(prompt).text
            mood = detect_mood(user_input)
            chat_entry = {"user": user_input, "reply": reply, "mood": mood}
            st.session_state.history.append(chat_entry)
            save_to_firebase(st.session_state.history, "chat_history")
            st.experimental_rerun = lambda: None  # dummy placeholder

# -----------------------
# Mood Overview Tab
# -----------------------
with tab2:
    if st.session_state.history:
        mood_counts = pd.Series([c["mood"] for c in st.session_state.history]).value_counts()
        st.bar_chart(mood_counts)
    else:
        st.info("No chat data yet to display mood overview.")

# -----------------------
# Self-Reflection Tab
# -----------------------
with tab3:
    # Add reflection
    with st.form(key="reflection_form", clear_on_submit=True):
        reflection_text = st.text_area("Write your reflection here:", key="reflection_box")
        submitted_reflection = st.form_submit_button("Save Reflection")
        if submitted_reflection and reflection_text.strip():
            st.session_state.reflections.append(reflection_text.strip())
            save_to_firebase(st.session_state.reflections, "reflections")

    # Display and delete reflections
    if st.session_state.reflections:
        for i, ref in enumerate(st.session_state.reflections):
            col1, col2 = st.columns([9,1])
            with col1:
                st.markdown(f"{i+1}. {ref}")
            with col2:
                if st.button("🗑", key=f"delete_ref_{i}"):
                    st.session_state.reflections.pop(i)
                    save_to_firebase(st.session_state.reflections, "reflections")
    else:
        st.info("No reflections saved yet.")
