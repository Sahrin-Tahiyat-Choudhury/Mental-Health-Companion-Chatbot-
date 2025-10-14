import streamlit as st
import openai
import json
from firebase_admin import credentials, initialize_app, db

# --- FIREBASE INITIALIZATION ---
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
cred = credentials.Certificate(firebase_key_dict)
initialize_app(cred, {"databaseURL": st.secrets["FIREBASE_DATABASE_URL"]})

# --- PAGE CONFIG ---
st.set_page_config(page_title="CalmMate Chatbot", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🌙 CalmMate")
st.sidebar.markdown("Your personal mental health companion 💬")
st.sidebar.divider()

# --- NICKNAME SETUP ---
if "nickname" not in st.session_state:
    st.session_state.nickname = ""

nickname_input = st.sidebar.text_input("Give your chatbot a nickname:", st.session_state.nickname)
if nickname_input:
    st.session_state.nickname = nickname_input
else:
    st.session_state.nickname = "CalmMate"

st.sidebar.write(f"🤖 Chatbot Name: *{st.session_state.nickname}*")

# --- TABS ---
tab_chat, tab_mood, tab_journal = st.tabs(["💬 Chat", "📊 Mood Overview", "📝 Journal"])

# --- AI RESPONSE FILTER (for haram suggestions) ---
def clean_response(text):
    forbidden_words = [
        "music", "songs", "playlist", "yoga", "meditation with music", "zodiac",
        "astrology", "manifestation", "crystals", "dating", "boyfriend", "girlfriend",
        "alcohol", "tarot", "luck", "superstition"
    ]
    for word in forbidden_words:
        if word.lower() in text.lower():
            text = text.replace(word, "⚠ [filtered suggestion]")
    return text

# --- CHAT SECTION ---
with tab_chat:
    st.title(f"Chat with {st.session_state.nickname}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            role, content = msg
            if role == "user":
                st.markdown(
                    f"<div style='text-align:right; color:#E0E0E0; background-color:#222; "
                    f"padding:10px; border-radius:10px; margin:5px 0;'>{content}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='text-align:left; color:#C0C0C0; background-color:#111; "
                    f"padding:10px; border-radius:10px; margin:5px 0;'><b>{st.session_state.nickname}:</b> {content}</div>",
                    unsafe_allow_html=True,
                )

    user_input = st.chat_input("Type your message...")

    if user_input:
        st.session_state.messages.append(("user", user_input))

        # --- AI Response Section ---
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional mental health assistant. Do not suggest anything haram like music, dating, yoga, etc."},
                    *[
                        {"role": role, "content": content}
                        for role, content in st.session_state.messages
                    ],
                ],
            )

            bot_message = response.choices[0].message.content
            bot_message = clean_response(bot_message)

            st.session_state.messages.append(("assistant", bot_message))

        except Exception as e:
            st.error("⚠ Something went wrong while generating a response.")
            st.write(e)

        st.rerun()

    if st.button("Clear Chat 🧹"):
        st.session_state.messages = []
        st.rerun()

# --- MOOD OVERVIEW TAB ---
with tab_mood:
    st.header("📊 Mood Overview")
    st.markdown("Your progress and emotional patterns will be visualized here soon, in shaa’ Allah.")

# --- JOURNAL TAB ---
with tab_journal:
    st.header("📝 Journal")
    st.text_area("Write your reflections or thoughts here:", height=250)
    st.markdown("Your journal entries are private and never shared.")
