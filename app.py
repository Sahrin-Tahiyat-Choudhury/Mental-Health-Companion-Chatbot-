import streamlit as st
import datetime
import plotly.express as px
import pandas as pd

# Initialize session state
if "reflections" not in st.session_state:
    st.session_state.reflections = []

if "mood_data" not in st.session_state:
    st.session_state.mood_data = []

if "reflection_temp" not in st.session_state:
    st.session_state.reflection_temp = ""

if "chat_temp" not in st.session_state:
    st.session_state.chat_temp = ""

st.title("💬 Self Reflection & Mood Tracker")

# Tabs
tab1, tab2, tab3 = st.tabs(["💭 Self Reflection", "📊 Mood Graph", "🤖 Chat Assistant"])

# --- Self Reflection Tab ---
with tab1:
    st.subheader("🪞 Reflect on Your Day")

    reflection = st.text_area("Write your reflection:", key="reflection_temp", placeholder="Type your thoughts here...")

    if st.button("Save Reflection"):
        if reflection.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.reflections.append({"time": timestamp, "text": reflection})
            st.success("✅ Reflection saved!")

            # Clear the text area safely
            st.session_state.reflection_temp = ""
            st.rerun()
        else:
            st.warning("⚠ Please write something before saving.")

    if st.session_state.reflections:
        st.write("### 📜 Saved Reflections")
        for i, entry in enumerate(st.session_state.reflections):
            st.markdown(f"🕒 {entry['time']}")
            st.write(entry['text'])
            if st.button(f"🗑 Delete {entry['time']}", key=f"delete_{i}"):
                st.session_state.reflections.pop(i)
                st.rerun()

# --- Mood Graph Tab ---
with tab2:
    st.subheader("📈 Mood Tracker")

    mood = st.selectbox("How are you feeling today?", ["😊 Happy", "😐 Neutral", "😞 Sad"], key="mood_selector")

    if st.button("Save Mood"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        st.session_state.mood_data.append({"date": timestamp, "mood": mood})
        st.success("✅ Mood saved successfully!")

    if st.session_state.mood_data:
        df = pd.DataFrame(st.session_state.mood_data)
        fig = px.histogram(df, x="date", color="mood", title="Mood Over Time")
        st.plotly_chart(fig, use_container_width=True)

# --- Chat Assistant Tab ---
with tab3:
    st.subheader("💬 AI Chat Assistant")

    user_input = st.text_input("Ask something or share your thoughts:", key="chat_temp")

    if st.button("Send"):
        if user_input.strip():
            st.write(f"*You:* {user_input}")
            st.write("*AI:* That's a thoughtful reflection. Keep going strong 💪")

            # Clear safely and rerun
            st.session_state.chat_temp = ""
            st.rerun()
        else:
            st.warning("Please type something before sending.")
