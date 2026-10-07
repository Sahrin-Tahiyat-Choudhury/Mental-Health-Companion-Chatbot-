Mental Health Companion Chatbot

An AI-powered mental health companion designed to provide accessible, supportive conversations for students and young adults experiencing academic stress, anxiety, or isolation.

📌 Problem Statement

Students and young adults often face stress, anxiety, and isolation due to heavy academic pressure and limited access to mental-health support. Traditional support systems can sometimes be inaccessible, stigmatized, or overburdened.

Problem: There is a need for an easy-to-use and empathetic AI companion that can provide emotional support, coping strategies, and guidance, particularly for individuals who may be hesitant to seek help in person.

💡 Project Overview

The Mental Health Companion Chatbot provides an interactive space where users can communicate with an AI companion, receive supportive responses, identify the mood expressed in their messages, and use a self-reflection feature.

The application is built using Streamlit, Python, Google Gemini 2.5 Flash-Lite, and Firebase Realtime Database.

«Disclaimer: This project is an educational prototype and is not a substitute for professional mental-health care, diagnosis, treatment, or emergency services.»

✨ Features

💬 AI Companion Chat

- Interactive chat interface built with Streamlit.
- AI-generated responses powered by Google Gemini 2.5 Flash-Lite.
- Responses are designed to maintain a calm, neutral, compassionate, and supportive tone.
- Customizable AI companion nickname.

🧠 Mood Detection

The chatbot automatically identifies the mood expressed in a user's message.

The current implementation supports six mood categories:

- Happy
- Sad
- Stressed
- Anxious
- Neutral
- Excited

The detected mood is displayed alongside the conversation.

📊 Mood Overview

- Provides an overview of the moods detected during the current conversation.
- Displays the distribution of detected moods through a chart.

✍️ Self-Reflection

- Allows users to write personal reflections.
- Reflections are timestamped.
- Users can view and delete their reflections during the current session.

⚙️ Settings

- Allows users to customize the AI companion's nickname.

☁️ Firebase Integration

- Chat history is stored using Firebase Realtime Database.
- Users can clear their stored chat history through the application.

🏗️ System Approach

Frontend

Streamlit

A Streamlit application provides the user interface, including:

- Chat interface
- User input and AI response display
- Mood Overview
- Self-Reflection
- Settings

Backend

Python

Python handles the application's chat logic, AI interactions, mood detection, and session-based functionality.

Model Engine

Google Gemini 2.5 Flash-Lite

Gemini is integrated through Google's Generative AI API to:

- Generate supportive conversational responses.
- Classify the mood expressed in user messages.

Data Handling

Firebase Realtime Database

Firebase Realtime Database is used to store chat history.

🔄 Algorithm & Application Flow

1. User sends a message through the chat interface.
2. AI generates a response using Google Gemini 2.5 Flash-Lite with instructions to respond in a calm and supportive manner.
3. Mood is detected automatically and classified as Happy, Sad, Stressed, Anxious, Neutral, or Excited.
4. Conversation data is stored in Firebase Realtime Database.
5. Mood information is displayed in the Mood Overview section.
6. Users can record reflections separately through the Self-Reflection section.

🛠️ Technology Stack

Technology| Purpose
Python| Application logic
Streamlit| User interface and web application
Google Gemini 2.5 Flash-Lite| AI responses and mood classification
Firebase Realtime Database| Chat-history storage

📁 Project Structure

Mental-Health-Companion-Chatbot-/
│
├── .devcontainer/
├── app.py
├── utils.py
├── requirements.txt
└── README.md

"app.py"

Contains the main application logic, including the Streamlit interface, Gemini integration, Firebase configuration, chat functionality, mood detection, self-reflection, and settings.

"utils.py"

Currently reserved for utility functionality.

"requirements.txt"

Contains the Python dependencies required to run the application.

🎨 Design Principles

🔐 Privacy & Security

The application is designed with privacy in mind and does not intentionally request unnecessary personal information. API credentials and Firebase configuration should be provided through secure application secrets rather than being hard-coded into the source code.

🕐 Always Available

The application is designed to provide accessible, on-demand interaction whenever the deployed service is available.

👤 User-Friendly

The interface is organized into clear sections for:

- Chat
- Mood Overview
- Self-Reflection
- Settings

This keeps the core functionality simple and easy to navigate.

⚠️ Current Limitations

The current version is an educational prototype.

- It does not provide professional diagnosis or treatment.
- It does not include a dedicated crisis-intervention system.
- Self-reflections are currently session-based rather than persistently stored.
- Mood visualization currently focuses on the current conversation rather than long-term mood history.
- The application does not currently include user authentication or individual user profiles.

## Future Scope

• Safe Venting Space

Introduce a dedicated Journal Mode where users can freely express their thoughts and the AI focuses primarily on reflecting the emotions expressed rather than immediately providing advice.

This could provide a space for users to process their feelings through guided reflection.

• Support More Languages

Add support for Arabic and other widely used languages so that students from different parts of the world can interact with the companion in languages they are comfortable using.

• Study & Focus Support

Introduce short micro-coaching sessions focused on productivity, study habits, and maintaining focus during academic work.

• Emotion Visualization

Expand mood visualization to show mood patterns over time, including color-coded representations of emotional intensity.

• Peer-Free Anti-Bullying Reflection

Introduce specialized journaling prompts to help students reflect on experiences involving bullying or social stress.

The AI could identify emotionally charged phrases and provide appropriate coping-oriented suggestions.

• Gamified Self-Care

Introduce lightweight gamification, such as:

- Daily streaks
- Small milestones
- Positive reinforcement for consistent self-reflection

The goal would be to encourage healthy engagement without making the experience competitive.

## Future Vision

The long-term goal is to evolve the chatbot from a basic conversational prototype into a more accessible and supportive AI companion for students, while maintaining a strong focus on responsible AI use, privacy, accessibility, and user well-being.

## Getting Started

Prerequisites

- Python 3.x
- Google Gemini API key
- Firebase project with Realtime Database configured

Installation

Clone the repository:

git clone https://github.com/Sahrin-Tahiyat-Choudhury/Mental-Health-Companion-Chatbot-.git
cd Mental-Health-Companion-Chatbot-

Install the required dependencies:

pip install -r requirements.txt

Configuration

Configure the required Gemini and Firebase credentials using Streamlit secrets.

Example:

GOOGLE_API_KEY = "your_google_api_key"
FIREBASE_KEY_JSON = "your_firebase_service_account_json"
FIREBASE_DATABASE_URL = "your_firebase_database_url"

Never commit API keys, Firebase credentials, or other secrets to the repository.

Run the Application

streamlit run app.py

📌 Project Status

This project was developed as part of an AI & Cloud internship project.

The current version demonstrates the integration of:

- Generative AI
- Conversational AI
- Mood classification
- Streamlit
- Firebase Realtime Database
- Python

📝 Conclusion

The Mental Health Companion Chatbot combines AI with an intuitive interface to offer accessible, on-demand emotional support.

It empowers users to express themselves, explore their moods, and access supportive guidance through a simple conversational interface.

The project demonstrates how generative AI and cloud technologies can be combined to explore accessible mental-health support for students and young adults, while also providing a foundation for future improvements such as multilingual support, study assistance, emotion visualization, safe venting, anti-bullying reflection, and gamified self-care.

📄 License

No license has currently been specified for this repository.
