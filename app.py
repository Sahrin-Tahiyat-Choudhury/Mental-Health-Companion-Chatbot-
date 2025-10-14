# app.py (Phase 5 - Chat + Reflection + Mood Insights)
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json
import html

# -------------------- Config / Secrets --------------------
load_dotenv()
# Use Streamlit secrets first, then fallback to env for local testing
API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
FIREBASE_KEY_JSON = st.secrets.get("FIREBASE_KEY_JSON") or os.getenv("FIREBASE_KEY_JSON")
FIREBASE_DB_URL = st.secrets.get("FIREBASE_DB_URL") or os.getenv("FIREBASE_DB_URL")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Initialize Firebase (if not already)
if not firebase_admin._apps:
    firebase_key_dict = json.loads(FIREBASE_KEY_JSON)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

# -------------------- Page UI --------------------
st.set_page_config(page_title="CalmMate - Mental Health Companion", page_icon="💬", layout="centered")
st.title("💬 CalmMate — Mental Health Companion")

# -------------------- Sidebar: Nickname --------------------
with st.sidebar:
    st.header("Settings")
    nickname = st.text_input("AI Companion Nickname", value=st.session_state.get("nickname", "CalmMate"))
    st.markdown("---")
    st.markdown("Quick tips:")
    st.markdown("- Use the *Reflection* tab for short journaling prompts.")
    st.markdown("- Check *Mood Insights* to see trends and friendly suggestions.")
st.session_state["nickname"] = nickname.strip() or "CalmMate"

# -------------------- Session state init --------------------
if "history" not in st.session_state:
    st.session_state.history = []          # list of {"user","reply","mood"}
if "reflections" not in st.session_state:
    st.session_state.reflections = []      # list of {"prompt","entry","reply"}
if "cleared" not in st.session_state:
    st.session_state.cleared = False

# -------------------- Helpers --------------------
def safe_html(s: str) -> str:
    """Escape HTML so user text won't break layout."""
    return html.escape(s).replace("\n", "<br>")

def detect_mood(text: str) -> str:
    prompt = f"""
    Determine the mood of this user message. Respond with exactly ONE word from:
    Happy, Sad, Stressed, Anxious, Neutral, Excited

    Message: {text}
    """
    resp = model.generate_content(prompt)
    return resp.text.strip().splitlines()[0][:20]  # short guard

def generate_reply(user_input: str, nickname: str) -> str:
    prompt = f"""
    You are a calm, compassionate AI companion named {nickname}.
    Respond in a gentle, non-judgmental, supportive tone (2-3 sentences).
    Do not give medical advice or diagnoses. Keep things concise.

    User: {user_input}
    """
    resp = model.generate_content(prompt)
    return resp.text

def save_history_to_firebase():
    try:
        db.reference("chat_history").set(st.session_state.history)
    except Exception:
        # avoid crashing if Firebase issues on deploy; app still works locally
        pass

def save_reflections_to_firebase():
    try:
        db.reference("reflections").set(st.session_state.reflections)
    except Exception:
        pass

def mood_counts_df():
    if not st.session_state.history:
        return pd.DataFrame()
    s = pd.Series([c["mood"] for c in st.session_state.history])
    return s.value_counts()

def mood_insights():
    """Produce a few short, safe insights based on recent moods."""
    hist = [c["mood"] for c in st.session_state.history[-30:]]  # lookback
    if not hist:
        return ["No data yet — start a chat and CalmMate will offer insights here."]
    counts = pd.Series(hist).value_counts()
    insights = []
    # Most frequent mood
    top = counts.idxmax()
    insights.append(f"Most frequent recent mood: *{top}* ({counts.max()} occurrences).")
    # Detect rising worry
    last7 = pd.Series(hist[-7:]) if len(hist) >= 1 else pd.Series(hist)
    if len(last7) >= 3:
        if (last7 == "Anxious").sum() >= max(2, len(last7)//2):
            insights.append("You seem to have more *anxious* entries recently. Consider writing about what specifically causes anxiety — naming it can help.")
    # If happy increasing
    if len(hist) >= 6:
        first = pd.Series(hist[:len(hist)//2]).value_counts()
        second = pd.Series(hist[len(hist)//2:]).value_counts()
        if second.get("Happy", 0) > first.get("Happy", 0):
            insights.append("Your happy days are trending up — nice progress! Keep noticing what helps.")
    # Gentle actionable tips (non-medical)
    insights.append("Tip: Try small micro-actions when stressed — short walk, talk to a friend, or list one thing you solved today.")
    return insights

# -------------------- CSS for dark chat and scroll --------------------
st.markdown(
    """
    <style>
    .chat-window {
        max-height: 420px;
        overflow-y: auto;
        padding: 8px;
        border-radius: 8px;
        background-color: #0f1720;
    }
    .ai-bubble {
        background-color: #1f2937;
        color: #ffffff;
        padding: 10px;
        border-radius: 12px;
        margin-bottom: 8px;
        width: 72%;
        text-align: left;
    }
    .user-bubble {
        background-color: #2b3440;
        color: #ffffff;
        padding: 10px;
        border-radius: 12px;
        margin-bottom: 8px;
        width: 72%;
        margin-left: auto;
        text-align: right;
    }
    .mood-tag { color: #cbd5e1; font-size: 12px; }
    .small-muted { color: #94a3b8; font-size: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Tabs --------------------
tab_chat, tab_reflect, tab_insights = st.tabs(["💬 Chat", "✍ Reflection", "📊 Mood Insights"])

# -------------------- CHAT TAB --------------------
with tab_chat:
    st.subheader(f"Chat with {st.session_state['nickname']}")
    # clear button
    col_l, col_r = st.columns([1, 3])
    with col_l:
        if st.button("🗑 Clear Chat"):
            st.session_state.history = []
            save_history_to_firebase()
            st.success("Chat cleared!")
    with col_r:
        st.write("")  # placeholder for alignment

    # chat window (scrollable)
    chat_html = "<div class='chat-window'>"
    for entry in st.session_state.history:
        user_html = safe_html(entry["user"])
        reply_html = safe_html(entry["reply"])
        mood = entry.get("mood", "Neutral")
        mood_emoji_map = {"Happy":"😊","Sad":"😢","Stressed":"😟","Anxious":"😰","Neutral":"😐","Excited":"😃"}
        mood_emoji_char = mood_emoji_map.get(mood, "😐")
        # user bubble then AI bubble below it (user on right)
        chat_html += f"<div class='user-bubble'><b>You</b><div style='margin-top:6px'>{user_html}</div></div>"
        chat_html += f"<div class='ai-bubble'><b>{st.session_state['nickname']}</b><div style='margin-top:6px'>{reply_html}</div>"
        chat_html += f"<div class='mood-tag'>Mood: {mood} {mood_emoji_char}</div></div>"
    chat_html += "</div>"

    st.markdown(chat_html, unsafe_allow_html=True)

    # Input form at bottom (keeps input below the chat window)
    with st.form("chat_input_form", clear_on_submit=True):
        user_msg = st.text_input("Your message", placeholder="Type something... (2–3 sentences is fine)")
        send = st.form_submit_button("Send")

        if send and user_msg and user_msg.strip():
            # generate reply and mood immediately (before rerender)
            reply = generate_reply(user_msg, st.session_state["nickname"])
            mood = detect_mood(user_msg)

            # append immediately
            st.session_state.history.append({"user": user_msg, "reply": reply, "mood": mood})
            save_history_to_firebase()
            # Streamlit will rerun and show the new chat above without experimental rerun.

# -------------------- REFLECTION TAB --------------------
with tab_reflect:
    st.subheader("Daily Reflection")
    st.markdown("Short prompts to help you reflect. Answer in a sentence or two; CalmMate will respond supportively.")

    # pick a prompt based on last mood (simple)
    last_mood = st.session_state.history[-1]["mood"] if st.session_state.history else "Neutral"
    prompt_map = {
        "Happy": "What made you smile today? Describe it briefly.",
        "Sad": "Tell me one small thing that felt a bit better today, however small.",
        "Stressed": "What is one small step you can take right now to ease some stress?",
        "Anxious": "Can you name one specific worry, even briefly? Naming it can help.",
        "Neutral": "What's one thing you did today that you want to remember?",
        "Excited": "What's one exciting thing you want to build on tomorrow?"
    }
    reflect_prompt = prompt_map.get(last_mood, "What's one thing you're grateful for today?")

    st.markdown(f"*Prompt:* {reflect_prompt}")
    reflection_input = st.text_area("Write your reflection (short):", key="reflection_input")

    if st.button("Share Reflection"):
        if reflection_input and reflection_input.strip():
            # AI responds supportively
            support_prompt = f"""
            You are a calm, supportive companion. A user wrote the following reflection:
            \"\"\"{reflection_input}\"\"\"
            Reply in 2-3 supportive sentences, acknowledge their feelings, and offer one gentle, practical idea (not medical).
            """
            support = model.generate_content(support_prompt).text
            st.session_state.reflections.append({"prompt": reflect_prompt, "entry": reflection_input, "reply": support})
            save_reflections_to_firebase()
            st.success("Reflection saved — CalmMate replied below.")
            st.markdown(f"*CalmMate:* {safe_html(support)}", unsafe_allow_html=True)
        else:
            st.warning("Write something first (a sentence or two is enough).")

# -------------------- MOOD INSIGHTS TAB --------------------
with tab_insights:
    st.subheader("Mood Insights")
    if st.session_state.history:
        counts = mood_counts_df()
        # display colored bar chart with simple table
        st.markdown("*Mood Counts*")
        df = pd.DataFrame({"count": counts})
        st.bar_chart(df["count"])

        st.markdown("*Insights & Friendly Suggestions*")
        for insight in mood_insights():
            st.markdown(f"- {insight}")
    else:
        st.info("No chat data yet. Talk to CalmMate to populate mood insights.")

# -------------------- End --------------------
