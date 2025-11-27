# Outfyt AI | Style Companion

**Outfyt AI** is an intelligent, context-aware fashion assistant designed to help users elevate their style. It combines advanced AI chat capabilities with practical tools like a digital wardrobe, outfit planner, and color analysis to provide a comprehensive personal styling experience.

## ✨ Key Features

- **🤖 AI Fashion Chatbot**: A context-aware assistant powered by Groq (LLM) that remembers your style preferences and conversation history.
- **🗣️ Voice Interaction**: Speak to Outfyt in English, Tamil, or Hindi! Powered by Groq Whisper for accurate transcription and gTTS for natural responses.
- **🧥 Digital Wardrobe**: Upload and organize your clothes. The database-backed system (Supabase) allows for multi-user support and persistent storage.
- **📅 Smart Outfit Planner**: Automatically generate outfit combinations for the week based on your wardrobe and local weather/events.
- **🎨 Color Analysis**: Discover your seasonal color palette (12-Season Logic) to find the colors that suit you best.
- **📸 Aesthetic Story Studio**: Generate "Instagram-ready" stories of your outfits with a single click.

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend/Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **AI/LLM**: [Groq API](https://groq.com/) (Llama 3 / Mixtral)
- **Voice**: Groq Whisper (STT) & gTTS (TTS)
- **Language**: Python

## 🚀 Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd MensFashionBot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up secrets:**
    Create a file named `.streamlit/secrets.toml` in the project root and add your API keys (see below).

4.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## 🔐 Secrets Setup

To run Outfyt AI, you need to configure the following secrets in `.streamlit/secrets.toml`:

```toml
# .streamlit/secrets.toml

# Groq API Key for LLM and Whisper
GROQ_API_KEY = "your_groq_api_key_here"

# Supabase Database Connection
# You can find this in your Supabase project settings -> Database -> Connection String -> URI
SUPABASE_DB_URL = "postgresql://user:password@host:port/database"
```

## 🗺️ Future Roadmap

- **Brand Integrations**: Direct shopping links and inventory integration with brands like **Peter England**.
- **Google Authentication**: Secure and seamless sign-in experience using Google OAuth.
- **Community Features**: Share outfits and get feedback from the Outfyt community.
