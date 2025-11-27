import streamlit as st
import base64
from groq import Groq
import time
from gtts import gTTS
import io
import json
import re
import os
import uuid
import datetime
from datetime import timedelta
from duckduckgo_search import DDGS
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from sqlalchemy import text
import random
import pandas as pd

# --- App Configuration ---
st.set_page_config(page_title="Outfyt AI - Style Companion", page_icon="assets/logo.png", layout="wide")

st.markdown("""
<style>
    /* --- MASTER THEME BLOCK --- */
    
    /* 1. Global Reset & Background */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed !important;
        color: #E0E0E0;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* 2. Text Visibility (Global) */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stCaption, li, div {
        color: #ffffff !important;
    }

    /* 3. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 4. Sidebar Arrow Fix (Solid Box Style) */
    [data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"] {
        color: #C5B358 !important;
        background-color: #1a1a2e !important;
        border: 2px solid #C5B358 !important;
        border-radius: 8px !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        width: 2.5rem !important;
        height: 2.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 0 10px rgba(197, 179, 88, 0.3) !important;
    }
    [data-testid="stSidebarCollapseButton"] *, [data-testid="stSidebarCollapsedControl"] * {
        fill: #C5B358 !important;
        color: #C5B358 !important;
        stroke: #C5B358 !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover, [data-testid="stSidebarCollapsedControl"]:hover {
        background-color: #C5B358 !important;
        box-shadow: 0 0 15px rgba(197, 179, 88, 0.6) !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover *, [data-testid="stSidebarCollapsedControl"]:hover * {
        fill: #1a1a2e !important;
        color: #1a1a2e !important;
        stroke: #1a1a2e !important;
    }
    
    /* Force the collapsed sidebar button to match */
    /* Force the collapsed sidebar button to match */
    [data-testid="stSidebarCollapsedControl"] {{
        background-color: #1a1a2e !important;
        border: 2px solid #C5B358 !important;
        border-radius: 8px !important;
        color: #C5B358 !important;
    }}
    [data-testid="stSidebarCollapsedControl"] svg, [data-testid="stSidebarCollapsedControl"] i {{
        color: #C5B358 !important;
        fill: #C5B358 !important;
    }}

    /* 5. Buttons (Gold Theme) */
    div.stButton > button:not([kind="primary"]), div.stFormSubmitButton > button:not([kind="primary"]) {
        background-color: #1a1a2e !important; 
        color: #C5B358 !important; 
        border: 2px solid #C5B358 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    div.stButton > button:not([kind="primary"]):hover {
        background-color: #C5B358 !important;
        color: #1a1a2e !important;
    }
    /* Primary Button (Red) */
    button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }

    /* 6. Inputs & Selectboxes */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div, div[data-baseweb="base-input"] {
        background-color: #262730 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-color: #444 !important;
    }
    
    /* 7. Dropdowns & Menus */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #262730 !important;
    }
    li[role="option"] {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    li[role="option"]:hover {
        background-color: #C5A059 !important;
    }

    /* 8. Dialogs & Modals (The Nuclear Fix) */
    div[data-testid="stDialog"], div[role="dialog"] {
        background-color: #1a1a2e !important;
        color: white !important;
    }
    div[data-testid="stDialog"] > div, div[role="dialog"] > div {
        background-color: #1a1a2e !important;
        color: white !important;
        border: 2px solid #C5B358 !important;
        border-radius: 15px !important;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] p, div[data-testid="stDialog"] label {
        color: #ffffff !important;
    }
    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #ffffff !important;
        background-color: transparent !important;
    }
    
    /* 9. File Uploader */
    [data-testid="stFileUploader"] button {
        color: #1a1a2e !important;
        background-color: #ffffff !important;
    }

    /* 10. Expander */
    [data-testid="stExpander"] details > summary {
        color: #ffffff !important;
        background-color: #2a2a4e !important;
        border: 1px solid #C5B358 !important;
    }

    /* 11. Chat Input Fix (Super Nuclear) */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
    }
    
    /* Target the internal wrapper provided by BaseWeb - Force BLACK */
    [data-testid="stChatInput"] div[data-baseweb="base-input"] {
        background-color: #000000 !important; /* Pure Black */
        border: 2px solid #C5B358 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    }

    /* The actual textarea - Force BLACK background, WHITE text */
    [data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #ffffff !important;
        caret-color: #C5B358 !important;
    }

    /* Placeholder Text */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #aaaaaa !important;
    }

    /* Send Button */
    [data-testid="stChatInput"] button {
        color: #C5B358 !important;
        background-color: transparent !important;
        border: none !important;
    }
    [data-testid="stChatInput"] button:hover {
        color: #ffffff !important;
        background-color: rgba(197, 179, 88, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Database Initialization ---
def init_db():
    conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
    with conn.session as s:
        s.execute(text('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS wardrobe 
                     (id TEXT PRIMARY KEY, user_id INTEGER, category TEXT, gender TEXT, image_path TEXT, filename TEXT, added_at FLOAT)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS planner 
                     (date TEXT PRIMARY KEY, user_id INTEGER, outfit_data TEXT)'''))
        s.execute(text("INSERT INTO users (id, username) VALUES (1, 'default_user') ON CONFLICT (id) DO NOTHING"))
        s.commit()

init_db()

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "stop_generating" not in st.session_state:
    st.session_state.stop_generating = False
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "is_signed_in" not in st.session_state:
    st.session_state.is_signed_in = False
if "last_audio_input" not in st.session_state:
    st.session_state.last_audio_input = None
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0
if "audio_cache" not in st.session_state:
    st.session_state.audio_cache = {}
if "playing_audio_id" not in st.session_state:
    st.session_state.playing_audio_id = None
if "user_season" not in st.session_state:
    st.session_state.user_season = None
if "wardrobe" not in st.session_state:
    st.session_state.wardrobe = []
if "planner" not in st.session_state:
    st.session_state.planner = {}

# New State Variables
if "show_voice_ui" not in st.session_state:
    st.session_state.show_voice_ui = False
if "show_upload_dialog" not in st.session_state:
    st.session_state.show_upload_dialog = False
if "gender_mode" not in st.session_state:
    st.session_state.gender_mode = "Men's Fashion"
if "prev_mode" not in st.session_state:
    st.session_state.prev_mode = st.session_state.gender_mode
if "shopping_results" not in st.session_state:
    st.session_state.shopping_results = {}
if "language" not in st.session_state:
    st.session_state.language = "English (US)"

# --- Authentication ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Groq API Key not found. Please check your .streamlit/secrets.toml file.")
    st.stop()

# --- Sidebar & Mode Selection ---
with st.sidebar:
    col_logo, col_title = st.columns([2, 3])
    with col_logo:
        st.image("assets/logo.png", width=180)
    with col_title:
        st.markdown("<h3 style='margin-top: 20px; margin-bottom: 10; font-size: 22px;'>Style Companion</h3>", unsafe_allow_html=True)
    
    # 1. The Switch (Sidebar Toggle)
    mode = st.radio(
        "Mode", 
        ["Men's Fashion", "Women's Fashion"], 
        horizontal=True, 
        key="gender_mode_radio"
    )
    st.session_state.gender_mode = mode
    
    # Mode Switch Notification
    if st.session_state.gender_mode != st.session_state.prev_mode:
        if st.session_state.gender_mode == "Women's Fashion":
            st.toast("Activating Women's Style Mode... 💃", icon='✨')
        else:
            st.toast("Activating Gentleman's Mode... 👔", icon='🎩')
        st.session_state.prev_mode = st.session_state.gender_mode

    if st.button("✨ New Chat", use_container_width=True, type="primary"):
        if st.session_state.messages:
            st.session_state.chat_history.append(st.session_state.messages)
        st.session_state.messages = []
        st.session_state.msg_count = 0 
        st.session_state.audio_cache = {}
        st.session_state.playing_audio_id = None
        st.session_state.shopping_results = {}
        st.rerun()
        
    st.subheader("History")
    if not st.session_state.chat_history:
        st.caption("No recent chats.")
    else:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            # Use the first user message as the title
            title = "New Chat"
            for msg in chat:
                if msg["role"] == "user":
                    title = msg["content"][:20] + "..."
                    break
            if st.button(title, key=f"hist_{i}", use_container_width=True):
                st.session_state.messages = chat
                st.rerun()
    
    st.divider()

    
    if st.session_state.is_signed_in:
        st.write(f"**{st.session_state.user_name}**")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.is_signed_in = False
            st.session_state.user_name = None
            st.session_state.user_season = None 
            st.rerun()
    else:
        if st.button("Sign In with Google", use_container_width=True):
            st.session_state.temp_signin = True
            st.rerun()

# --- Dynamic Branding (Theme Shifting) ---
if st.session_state.gender_mode == "Men's Fashion":
    accent_color = "#C5A059" # Gold
    accent_hover = "#B08D45"
    text_highlight = "#000000"
else:
    accent_color = "#E0BFB8" # Soft Rose Gold
    accent_hover = "#D4AF37" # Gold/Rose mix
    text_highlight = "#333333"

# --- CSS Injection ---
st.markdown(f"""
<style>
    /* Global Reset & Background */
    html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed !important;
        color: #E0E0E0;
        font-family: 'Helvetica Neue', sans-serif;
    }}
    
    /* Main App Container */
    .stApp {{
        background: transparent !important;
    }}

    /* Header (Transparent) */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* Text Colors */
    .stMarkdown, .stText, p, h1, h2, h3, label, div {{
        color: #E0E0E0 !important;
    }}
    
    /* Glass Buttons (General) */
    .stButton button {{
        background: linear-gradient(135deg, {accent_color} 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #764ba2 0%, {accent_color} 100%);
    }}

    /* Sidebar Link-Style Buttons */
    [data-testid="stSidebar"] .stButton button {{
        background: transparent !important;
        box-shadow: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding-left: 0 !important;
        color: #B0B0B0 !important;
        font-weight: 400 !important;
    }}
    [data-testid="stSidebar"] .stButton button:hover {{
        color: #FFFFFF !important;
        background: rgba(255,255,255,0.05) !important;
        transform: none !important;
    }}
    /* Primary "New Chat" Button in Sidebar - Override Link Style */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {accent_color} 0%, #764ba2 100%) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        justify-content: center !important;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    
    /* User Message Specific Style */
    [data-testid="stChatMessage"]:nth-child(odd) {{
        background-color: rgba(118, 75, 162, 0.15);
        border: 1px solid rgba(118, 75, 162, 0.3);
    }}

    /* Dividers */
    hr {{
        border-color: rgba(255, 255, 255, 0.2);
    }}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {{
        width: 8px;
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(118, 75, 162, 0.5);
        border-radius: 10px;
    }}

    /* --- On-Demand Audio Button Styling (Dynamic) --- */
    .stChatMessage .stButton button {{
        background: transparent !important;
        border: 2px solid {accent_color} !important;
        color: {accent_color} !important;
        border-radius: 20px !important;
        padding: 0.3rem 1rem !important;
        font-size: 0.9rem !important;
        box-shadow: 0 0 10px rgba(197, 160, 89, 0.1) !important;
        transition: all 0.3s ease !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    .stChatMessage .stButton button:hover {{
        background: rgba(197, 160, 89, 0.1) !important;
        box-shadow: 0 0 20px rgba(197, 160, 89, 0.4) !important;
        transform: scale(1.05) !important;
        color: #FFF !important;
    }}

    /* --- Waveform Animation CSS --- */
    .waveform {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        height: 30px;
        gap: 4px;
        margin-top: 10px;
    }}
    
    .bar {{
        width: 4px;
        background-color: {accent_color};
        border-radius: 2px;
        animation: wave 1s ease-in-out infinite;
    }}
    
    .bar:nth-child(1) {{ animation-delay: 0.0s; height: 10px; }}
    .bar:nth-child(2) {{ animation-delay: 0.1s; height: 15px; }}
    .bar:nth-child(3) {{ animation-delay: 0.2s; height: 20px; }}
    .bar:nth-child(4) {{ animation-delay: 0.3s; height: 15px; }}
    .bar:nth-child(5) {{ animation-delay: 0.4s; height: 10px; }}
    
    @keyframes wave {{
        0%, 100% {{ transform: scaleY(1); }}
        50% {{ transform: scaleY(2); }}
    }}
    
    /* --- Color Swatch Styling --- */
    .color-swatch-container {{
        display: flex;
        gap: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }}
    .color-swatch {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        border: 2px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }}
    .color-swatch:hover {{
        transform: scale(1.2);
        border-color: #FFF;
    }}
    .season-title {{
        font-size: 2em;
        font-weight: bold;
        background: linear-gradient(to right, {accent_color}, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }}
    
    /* --- 1. GLOBAL INPUTS (Text, Date, Select) --- */
    /* Force the container of all inputs to be Dark Grey */
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] {{
        background-color: #262730 !important;
        color: #FAFAFA !important;
        border-color: #444 !important;
    }}
    /* Force text inside inputs to be White */
    input {{
        color: #FAFAFA !important;
    }}

    /* --- 2. DROPDOWNS & POPOVERS (The Menu Lists) --- */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-testid="stSelectboxVirtualDropdown"] {{
        background-color: #262730 !important;
    }}
    /* The individual options */
    li[role="option"] {{
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }}
    li[role="option"] div {{
        color: #FAFAFA !important;
    }}
    /* Hover State (Gold) */
    li[role="option"]:hover {{
        background-color: #C5A059 !important;
    }}
    li[role="option"]:hover div {{
        color: #000000 !important;
    }}

    /* --- 3. DATE PICKER (For the Planner) --- */
    div[data-baseweb="calendar"] {{
        background-color: #262730 !important;
    }}
    div[data-baseweb="calendar"] button {{
        color: #FAFAFA !important;
    }}

    /* --- 4. TOASTS (Notifications) --- */
    div[data-testid="stToast"] {{
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }}

    /* --- Wardrobe Gallery Styling --- */
    .wardrobe-item {{
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 10px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .wardrobe-item img {{
        border-radius: 10px;
        max-width: 100%;
        height: auto;
        object-fit: cover;
    }}
    .wardrobe-caption {{
        margin-top: 10px;
        font-weight: 600;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.8); /* Strong shadow for contrast */
        color: #FFFFFF !important;
        font-size: 1.1rem;
    }}
    /* Custom White Chat Input */
    .stChatInput textarea {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important;
        border: 2px solid #C5B358 !important;
    }}
    .stChatInput textarea::placeholder {{
        color: #666666 !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- Dialogs ---
if st.session_state.get("temp_signin"):
    @st.dialog("Sign In")
    def sign_in_dialog_func():
        st.write("Enter your Name to complete Sign In:")
        name = st.text_input("Name")
        if name:
            if st.button("Confirm"):
                st.session_state.user_name = name
                st.session_state.is_signed_in = True
                st.session_state.temp_signin = False
                st.rerun()
    sign_in_dialog_func()

@st.dialog("Sign In Required")
def sign_in_required_dialog():
    st.write("You've reached the free limit of 5 messages.")
    st.write("Sign in to continue chatting with Outfyt AI.")
    if st.button("Continue with Google", use_container_width=True):
        st.session_state.temp_signin = True
        st.rerun()

@st.dialog("Upload Outfit Photo")
def upload_dialog():
    st.write("Upload a photo for analysis.")
    uploaded = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    if uploaded:
        st.session_state.uploaded_file_temp = uploaded
        if st.button("Analyze", type="primary"):
            st.session_state.show_upload_dialog = False
            st.rerun()

# --- Helper Functions ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def transcribe_audio(audio_file):
    try:
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            prompt="The audio is likely in English, Hindi, or Tamil.",
            response_format="text",
            temperature=0.0
        )
        return transcription
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return None

def text_to_speech(text, lang_config):
    try:
        tts = gTTS(text=text, lang=lang_config['lang'], tld=lang_config.get('tld', 'com'))
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except Exception as e:
        st.error(f"Error generating speech: {e}")
        return None

def summarize_for_audio(text, language):
    try:
        system_prompt = f"""
        You are a fashion assistant. Convert the following advice into a short, spoken script in {language}.
        Rules:
        1. Do NOT say "Here is the summary" or "In this look".
        2. Just speak the advice directly and naturally.
        3. Keep it under 2 sentences.
        4. Output ONLY the spoken text in {language}.
        """
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=150
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error summarizing audio: {e}")
        return text 

def play_hidden_audio(audio_path):
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        md = f"""
            <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error playing audio: {e}")

def extract_json_from_text(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return json.loads(text)
    except:
        return None

def display_color_swatches(color_list):
    # color_list is now a list of dicts: [{"name": "...", "hex": "..."}, ...]
    cols = st.columns(len(color_list))
    for i, color in enumerate(color_list):
        with cols[i]:
            st.markdown(f"""
            <div style="background-color: {color['hex']}; width: 100%; height: 60px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"></div>
            <p style="text-align:center; font-size: 0.8rem; margin-top: 5px;">{color['name']}</p>
            """, unsafe_allow_html=True)

def save_item_to_wardrobe(image_file, category, gender):
    try:
        save_dir = "assets/wardrobe"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        file_ext = image_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(save_dir, unique_filename)
        
        with open(file_path, "wb") as f:
            f.write(image_file.getbuffer())
            
        new_id = str(uuid.uuid4())
        added_at = time.time()
        
        conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
        with conn.session as s:
            s.execute(
                text("INSERT INTO wardrobe (id, user_id, category, gender, image_path, filename, added_at) VALUES (:id, :user_id, :category, :gender, :image_path, :filename, :added_at)"),
                {"id": new_id, "user_id": 1, "category": category, "gender": gender, "image_path": file_path, "filename": unique_filename, "added_at": added_at}
            )
            s.commit()
        
        # Update session state cache
        new_item = {
            "id": new_id,
            "category": category,
            "gender": gender,
            "image_path": file_path,
            "filename": unique_filename,
            "added_at": added_at
        }
        st.session_state.wardrobe.append(new_item)
        return True
    except Exception as e:
        st.error(f"Error saving item: {e}")
        return False

def delete_item_from_wardrobe(item_id):
    try:
        conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
        with conn.session as s:
            s.execute(text("DELETE FROM wardrobe WHERE id=:id"), {"id": item_id})
            s.commit()
        
        # Update session state cache
        st.session_state.wardrobe = [item for item in st.session_state.wardrobe if item['id'] != item_id]
        return True
    except Exception as e:
        st.error(f"Error deleting item: {e}")
        return False

def save_plan(date_str, outfit_dict):
    try:
        # Add gender to the plan
        outfit_dict['gender'] = st.session_state.gender_mode
        
        conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
        with conn.session as s:
            s.execute(
                text("INSERT INTO planner (date, user_id, outfit_data) VALUES (:date, :user_id, :outfit_data) ON CONFLICT (date) DO UPDATE SET outfit_data = EXCLUDED.outfit_data"),
                {"date": date_str, "user_id": 1, "outfit_data": json.dumps(outfit_dict)}
            )
            s.commit()
        
        # Update session state cache
        st.session_state.planner[date_str] = outfit_dict
        return True
    except Exception as e:
        st.error(f"Error saving plan: {e}")
        return False

def get_plan(date_str):
    # Try cache first
    if date_str in st.session_state.planner:
        return st.session_state.planner[date_str]
        
    try:
        conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
        df = conn.query("SELECT outfit_data FROM planner WHERE date=:date AND user_id=1", params={"date": date_str}, ttl=0)
        
        if not df.empty:
            plan = json.loads(df.iloc[0]['outfit_data'])
            st.session_state.planner[date_str] = plan
            return plan
        return None
    except:
        return None

@st.cache_data(ttl=60)
def get_wardrobe_items(user_id):
    # Use session state cache which is populated/updated
    items = []
    
    # Handle None user_id gracefully
    if user_id is None:
        return []

    # If cache is empty but DB might have items (startup), load them
    if not st.session_state.wardrobe:
        try:
            conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
            # Fetch ALL items for this user (Men's and Women's mixed)
            df = conn.query("SELECT * FROM wardrobe WHERE user_id=:uid", params={"uid": user_id}, ttl=0)
            
            loaded_items = []
            for index, row in df.iterrows():
                loaded_items.append({
                    "id": row['id'],
                    "category": row['category'],
                    "gender": row['gender'],
                    "image_path": row['image_path'],
                    "filename": row['filename'],
                    "added_at": row['added_at']
                })
            st.session_state.wardrobe = loaded_items
        except:
            pass

    if st.session_state.wardrobe:
        # Return ALL items from cache, no filtering
        items = st.session_state.wardrobe
            
    return items

def search_fashion_items(keywords):
    try:
        results = []
        with DDGS() as ddgs:
            # 1. Trusted Sites Query
            trusted_query = f"{keywords} site:myntra.com OR site:amazon.in OR site:ajio.com"
            ddg_results = list(ddgs.images(trusted_query, region='in-en', max_results=3))
            
            # 2. Fallback: General India Search
            if not ddg_results:
                general_query = f"{keywords} buy online india"
                ddg_results = list(ddgs.images(general_query, region='in-en', max_results=3))
            
            for res in ddg_results:
                results.append({
                    "title": res.get("title", "Fashion Item"),
                    "image": res.get("image", ""),
                    "url": res.get("url", "#") 
                })
        return results
    except Exception as e:
        return []

def extract_shopping_keywords(text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": 'You are a search query generator. Output a JSON object with a single key "query". The value must be a concise product name based on the user\'s last request. Example: {"query": "Men Black Oxford Shoes"}. Do not add conversational text.'},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=50,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content
    except Exception as e:
        return json.dumps({"query": text[:50]}) # Fallback JSON

def generate_aesthetic_story(outfit_dict, date_str, layout, background, filter_effect):
    try:
        # 1. Canvas Setup
        width, height = 1080, 1920
        
        # Background Logic
        if background == "Solid Dark":
            img = Image.new('RGB', (width, height), (14, 17, 23))
        elif background == "Deep Navy":
            img = Image.new('RGB', (width, height), (10, 10, 30))
        elif background == "Midnight Noise":
            img = Image.new('RGB', (width, height), (5, 5, 10))
            noise = Image.effect_noise((width, height), 20).convert('RGB')
            img = Image.blend(img, noise, 0.15)
        elif background == "Marble White":
            img = Image.new('RGB', (width, height), (245, 245, 245))
            # Simple marble-like noise
            noise = Image.effect_noise((width, height), 5).convert('RGB')
            img = Image.blend(img, noise, 0.05)
        elif background == "Sunset Blur":
            img = Image.new('RGB', (width, height), (50, 20, 40))
            draw = ImageDraw.Draw(img)
            draw.ellipse((-200, -200, 1000, 1000), fill=(255, 100, 50), outline=None)
            draw.ellipse((200, 800, 1400, 2000), fill=(100, 20, 150), outline=None)
            img = img.filter(ImageFilter.GaussianBlur(150))
        elif background == "Aura Gradient (Blue/Purple)":
            img = Image.new('RGB', (width, height), (20, 10, 40))
            draw = ImageDraw.Draw(img)
            draw.ellipse((-200, -200, 800, 800), fill=(50, 20, 100), outline=None)
            draw.ellipse((400, 1000, 1400, 2000), fill=(20, 50, 120), outline=None)
            img = img.filter(ImageFilter.GaussianBlur(100))
        elif background == "Retro Grain":
            img = Image.new('RGB', (width, height), (40, 40, 40))
            noise = Image.effect_noise((width, height), 20).convert('RGB')
            img = Image.blend(img, noise, 0.1)
        else:
            img = Image.new('RGB', (width, height), (14, 17, 23))

        draw = ImageDraw.Draw(img)
        
        # 2. Fonts
        try:
            font_vibe = ImageFont.truetype("arial.ttf", 40)
            font_watermark = ImageFont.truetype("arial.ttf", 30)
        except:
            font_vibe = ImageFont.load_default()
            font_watermark = ImageFont.load_default()

        # 3. Load Images
        images = []
        for cat, item_id in outfit_dict.items():
            if cat in ['gender', 'note']: continue
            item = next((it for it in st.session_state.wardrobe if it['id'] == item_id), None)
            if item and os.path.exists(item['image_path']):
                try:
                    p_img = Image.open(item['image_path']).convert("RGBA")
                    
                    # Apply Filters
                    if filter_effect == "B&W Moody":
                        p_img = ImageOps.grayscale(p_img).convert("RGBA")
                        enhancer = ImageEnhance.Contrast(p_img)
                        p_img = enhancer.enhance(1.2)
                    elif filter_effect == "B&W High Contrast":
                        p_img = ImageOps.grayscale(p_img).convert("RGBA")
                        enhancer = ImageEnhance.Contrast(p_img)
                        p_img = enhancer.enhance(1.5)
                    elif filter_effect == "Warm Glow":
                        overlay = Image.new('RGBA', p_img.size, (255, 200, 150, 50))
                        p_img = Image.alpha_composite(p_img, overlay)
                    elif filter_effect == "Cool & Sharp":
                        overlay = Image.new('RGBA', p_img.size, (200, 220, 255, 40))
                        p_img = Image.alpha_composite(p_img, overlay)
                        enhancer = ImageEnhance.Sharpness(p_img)
                        p_img = enhancer.enhance(1.5)
                    elif filter_effect == "Vintage Grain":
                        enhancer = ImageEnhance.Color(p_img)
                        p_img = enhancer.enhance(0.8) # Desaturate slightly
                        # Add slight yellow tint
                        overlay = Image.new('RGBA', p_img.size, (255, 240, 200, 30))
                        p_img = Image.alpha_composite(p_img, overlay)
                        
                    images.append(p_img)
                except:
                    pass
        
        if not images: return None
        
        num_imgs = len(images)

        # 4. Layout Logic
        # Define safe area (padding)
        pad = 50
        safe_width = width - 2*pad
        safe_height = height - 300 # Leave space for bottom text
        start_y = 100
        
        if layout == "Auto-Grid (Smart)":
            if num_imgs == 1:
                # Full center
                target_size = (safe_width, int(safe_height * 0.8))
                img1 = ImageOps.fit(images[0], target_size, method=Image.BICUBIC)
                img.paste(img1, (pad, start_y))
                
            elif num_imgs == 2:
                # Top/Bottom Split
                h_split = safe_height // 2 - 10
                target_size = (safe_width, h_split)
                
                img1 = ImageOps.fit(images[0], target_size, method=Image.BICUBIC)
                img2 = ImageOps.fit(images[1], target_size, method=Image.BICUBIC)
                
                img.paste(img1, (pad, start_y))
                img.paste(img2, (pad, start_y + h_split + 20))
                
            elif num_imgs == 3:
                # Magazine Layout: Left Half (Full), Right Half (Split)
                w_split = safe_width // 2 - 10
                h_full = safe_height
                h_half = safe_height // 2 - 10
                
                # Image 1 (Left, Full)
                img1 = ImageOps.fit(images[0], (w_split, h_full), method=Image.BICUBIC)
                img.paste(img1, (pad, start_y))
                
                # Image 2 (Right Top)
                img2 = ImageOps.fit(images[1], (w_split, h_half), method=Image.BICUBIC)
                img.paste(img2, (pad + w_split + 20, start_y))
                
                # Image 3 (Right Bottom)
                img3 = ImageOps.fit(images[2], (w_split, h_half), method=Image.BICUBIC)
                img.paste(img3, (pad + w_split + 20, start_y + h_half + 20))
                
            elif num_imgs >= 4:
                # Quad Grid
                w_half = safe_width // 2 - 10
                h_half = safe_height // 2 - 10
                
                coords = [
                    (pad, start_y),
                    (pad + w_half + 20, start_y),
                    (pad, start_y + h_half + 20),
                    (pad + w_half + 20, start_y + h_half + 20)
                ]
                
                for i in range(4):
                    if i < len(images):
                        p_img = ImageOps.fit(images[i], (w_half, h_half), method=Image.BICUBIC)
                        img.paste(p_img, coords[i])

        elif layout == "Vertical Stack":
            # Simple vertical stack
            h_slot = (safe_height // num_imgs) - 20
            current_y = start_y
            for p_img in images:
                p_img_resized = ImageOps.fit(p_img, (safe_width, h_slot), method=Image.BICUBIC)
                img.paste(p_img_resized, (pad, current_y))
                current_y += h_slot + 20

        elif layout == "Polaroid Scatter":
            # Random scatter logic (simplified for stability)
            centers = []
            if num_imgs == 2: centers = [(width//2, 600), (width//2, 1200)]
            elif num_imgs == 3: centers = [(width//2 - 100, 500), (width//2 + 100, 900), (width//2 - 50, 1300)]
            elif num_imgs >= 4: centers = [(width//3, 500), (2*width//3, 500), (width//3, 1100), (2*width//3, 1100)]
            else: centers = [(width//2, 900)]
            
            for i, p_img in enumerate(images):
                if i >= len(centers): break
                
                # Resize for polaroid
                p_img.thumbnail((600, 600))
                
                # Create Frame
                frame_w, frame_h = p_img.width + 40, p_img.height + 100
                frame = Image.new('RGBA', (frame_w, frame_h), (255, 255, 255, 255))
                frame.paste(p_img, (20, 20), p_img)
                
                # Rotate
                angle = random.randint(-10, 10)
                frame = frame.rotate(angle, expand=True, resample=Image.BICUBIC)
                
                cx, cy = centers[i]
                x = cx - frame.width // 2
                y = cy - frame.height // 2
                
                # Paste with mask for transparency
                img.paste(frame, (x, y), frame)

        # 5. Text Overlays
        # Vibe Check
        vibe_text = "Vibe: Clean • Minimal • Sharp" # Placeholder logic
        w_vibe = draw.textlength(vibe_text, font=font_vibe)
        draw.text(((width - w_vibe) // 2, height - 150), vibe_text, fill="#FFFFFF", font=font_vibe)
        
        # Watermark
        watermark_text = "Styled by Outfyt AI"
        w_wm = draw.textlength(watermark_text, font=font_watermark)
        draw.text(((width - w_wm) // 2, height - 60), watermark_text, fill="#AAAAAA", font=font_watermark)
        
        # 6. Output
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Error generating story: {e}")
        return None

@st.dialog("Aesthetic Story Studio")
def story_studio_dialog(plan, day_display):
    st.write("Customize your OOTD Story vibe.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        layout = st.selectbox("Layout", ["Auto-Grid (Smart)", "Polaroid Scatter", "Vertical Stack"])
    with c2:
        bg = st.selectbox("Background", ["Solid Dark", "Deep Navy", "Midnight Noise", "Marble White", "Sunset Blur", "Aura Gradient (Blue/Purple)", "Retro Grain"])
    with c3:
        filt = st.selectbox("Filter", ["None", "Warm Glow", "Cool & Sharp", "Vintage Grain", "B&W Moody", "B&W High Contrast"])
        
    if st.button("🔄 Refresh Preview", use_container_width=True):
        st.rerun()
        
    # Generate Preview
    with st.spinner("Creating aesthetic..."):
        story_buf = generate_aesthetic_story(plan, day_display, layout, bg, filt)
        
    if story_buf:
        st.image(story_buf, caption="Preview", use_container_width=True)
        st.download_button(
            label="✨ Download Story",
            data=story_buf,
            file_name=f"ootd_story.png",
            mime="image/png",
            type="primary",
            use_container_width=True
        )

def delete_plan_day(date_str):
    try:
        conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
        with conn.session as s:
            s.execute(text("DELETE FROM planner WHERE date=:date AND user_id=1"), {"date": date_str})
            s.commit()
        
        # Update cache
        if date_str in st.session_state.planner:
            del st.session_state.planner[date_str]
        return True
    except Exception as e:
        st.error(f"Error deleting plan: {e}")
        return False

def clear_all_plans():
    try:
        conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
        with conn.session as s:
            s.execute(text("DELETE FROM planner WHERE user_id=1"))
            s.commit()
        
        # Clear cache
        st.session_state.planner = {}
        return True
    except Exception as e:
        st.error(f"Error clearing plans: {e}")
        return False

def generate_smart_plan(occasion, num_days):
    try:
        # 1. Get Wardrobe
        all_items = [item for item in st.session_state.wardrobe if item.get('gender', "Men's Fashion") == st.session_state.gender_mode]
        
        if not all_items:
            return False, "Wardrobe is empty!"

        # 2. Prepare Prompt
        items_json = json.dumps([{k: v for k, v in item.items() if k in ['id', 'category']} for item in all_items])
        
        system_prompt = f"""
        You are a Smart Stylist. Create a {num_days}-day outfit plan for a "{occasion}" occasion.
        
        Wardrobe: {items_json}
        
        Rules:
        1. Select a Top, Bottom, and Shoes for each day.
        2. Prioritize items strictly matching the occasion.
        3. FALLBACK LOGIC: If you run out of perfect matches, use the next best appropriate item.
        4. REASONING: For each day, provide a "style_reasoning" explaining why you chose this outfit (e.g., "Linen shirt for breathability").
        5. Variety: Try not to repeat the exact same outfit.
        6. Return JSON: {{ "Day 1": {{ "Top": "id", "Bottom": "id", "Shoes": "id", "style_reasoning": "..." }}, ... }}
        """
        
        start_date = datetime.date.today() + timedelta(days=1)
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Plan for {num_days} days starting {start_date}."}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        plan_json = json.loads(completion.choices[0].message.content)
        
        # 3. Save to DB
        current_date = start_date
        for day_key, outfit in plan_json.items():
            date_str = current_date.strftime("%Y-%m-%d")
            
            final_outfit = {}
            if "style_reasoning" in outfit:
                final_outfit["note"] = outfit["style_reasoning"]
            elif "note" in outfit:
                final_outfit["note"] = outfit["note"]
                
            for part in ["Top", "Bottom", "Shoes"]:
                item_id = outfit.get(part)
                if item_id:
                    found = next((it for it in all_items if it['id'] == item_id), None)
                    if found:
                        final_outfit[found['category']] = item_id
            
            save_plan(date_str, final_outfit)
            current_date += timedelta(days=1)
            
        return True, "Plan generated!"
        
    except Exception as e:
        return False, str(e)

def shuffle_day_plan(date_str, occasion):
    try:
        # Similar to generate but for 1 day
        all_items = [item for item in st.session_state.wardrobe if item.get('gender', "Men's Fashion") == st.session_state.gender_mode]
        items_json = json.dumps([{k: v for k, v in item.items() if k in ['id', 'category']} for item in all_items])
        
        system_prompt = f"""
        Pick a completely NEW outfit for "{occasion}" from this wardrobe.
        Wardrobe: {items_json}
        Return JSON: {{ "Top": "id", "Bottom": "id", "Shoes": "id", "note": "Refreshed look" }}
        """
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.9, # Higher temp for variety
            response_format={"type": "json_object"}
        )
        
        outfit = json.loads(completion.choices[0].message.content)
        
        final_outfit = {}
        if "note" in outfit:
            final_outfit["note"] = outfit["note"]
            
        for part in ["Top", "Bottom", "Shoes"]:
            item_id = outfit.get(part)
            if item_id:
                found = next((it for it in all_items if it['id'] == item_id), None)
                if found:
                    final_outfit[found['category']] = item_id
                    
        save_plan(date_str, final_outfit)
        return True
    except:
        return False

# --- Fragment for Chat Message Rendering ---
@st.fragment
def render_chat_message(message, i):
    # 1. Determine Avatar based on Role
    if message["role"] == "assistant":
        # Check if the file actually exists to prevent crashing
        if os.path.exists("assets/logo.png"):
            avatar_icon = "assets/logo.png"
        else:
            # If the file is missing/renamed, use a robot emoji fallback
            avatar_icon = "🤖" 
    else:
        # User Logic
        user_name = st.session_state.get("user_name", "User")
        if user_name and user_name != "User":
            # Use UI Avatars API to generate a dynamic image
            # This prevents the single-character crash in Streamlit
            avatar_icon = f"https://ui-avatars.com/api/?name={user_name}&background=C5B358&color=1a1a2e"
        else:
            avatar_icon = "👤"

    with st.chat_message(message["role"], avatar=avatar_icon):
        if isinstance(message["content"], str):
            st.markdown(message["content"])
        elif isinstance(message["content"], list):
             for part in message["content"]:
                 if part['type'] == 'text':
                     st.markdown(part['text'])
                 elif part['type'] == 'image_url':
                     pass
        
        if message["role"] == "assistant":
            if st.session_state.playing_audio_id == i:
                st.markdown("""
                <div class="waveform">
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                </div>
                """, unsafe_allow_html=True)
                
                if i in st.session_state.audio_cache:
                    play_hidden_audio(st.session_state.audio_cache[i])
                
                if st.button("Stop Audio", key=f"stop_audio_{i}"):
                    st.session_state.playing_audio_id = None
                    st.rerun()
                    
            else:
                c_listen, c_spacer = st.columns([1, 4])
                with c_listen:
                    if st.button("🔊 Listen", key=f"tts_{i}"):
                        if i not in st.session_state.audio_cache:
                            with st.spinner("Generating voice..."):
                                text_content = message["content"]
                                if isinstance(text_content, list):
                                    text_content = next((p['text'] for p in text_content if p['type'] == 'text'), "")
                                
                                # Determine language for TTS
                                lang_code = message.get("lang_code", "en")
                                
                                # Map common Indian languages to co.in for better accent
                                tld = "co.in" if lang_code in ['ta', 'hi', 'ml', 'kn', 'te'] else "com"
                                lang_config = {"lang": lang_code, "tld": tld}
                                
                                # Use pre-generated summary if available, else generate one
                                summary = message.get("speech_summary")
                                if not summary:
                                    summary = summarize_for_audio(text_content, lang_code)
                                
                                # Generate Audio File (Unique Name)
                                try:
                                    # Cleanup old files
                                    audio_dir = "static/audio"
                                    if not os.path.exists(audio_dir):
                                        os.makedirs(audio_dir)
                                    
                                    for f in os.listdir(audio_dir):
                                        if f.endswith(".mp3"):
                                            try:
                                                os.remove(os.path.join(audio_dir, f))
                                            except: pass

                                    unique_filename = f"audio_{uuid.uuid4()}.mp3"
                                    file_path = os.path.join(audio_dir, unique_filename)
                                    
                                    tts = gTTS(text=summary, lang=lang_config['lang'], tld=lang_config.get('tld', 'com'))
                                    tts.save(file_path)
                                    
                                    st.session_state.audio_cache[i] = file_path
                                except Exception as e:
                                    st.error(f"Error generating audio: {e}")
                                
                        st.session_state.playing_audio_id = i
                        st.rerun()

# --- Fragment for Main Chat Interface ---
@st.fragment
def render_chat_interface():
    # Display Chat History
    for i, message in enumerate(st.session_state.messages):
        render_chat_message(message, i)

    st.write("") # Spacer
    st.write("") 
    
    # Action Bar Container
    c1, c2, c3 = st.columns([1, 10, 1])
    with c1:
        if st.button("📷", key="btn_upload_main", help="Analyze an Outfit"):
            upload_dialog()
            
    with c3:
        if st.button("🎤", key="btn_voice_main", help="Toggle Voice Mode"):
            st.session_state.show_voice_ui = not st.session_state.show_voice_ui
            st.rerun()
            
    # Voice UI
    audio_prompt = None
    if st.session_state.show_voice_ui:
        st.markdown("### 🎙️ Voice Mode")
        audio_input = st.audio_input("Speak now...", key=f"audio_{st.session_state.audio_key}")
        if audio_input:
            with st.spinner("Listening..."):
                transcribed_text = transcribe_audio(audio_input)
                if transcribed_text:
                    audio_prompt = transcribed_text

    # Chat Logic
    prompt = None
    
    # Check Voice Prompt first
    if audio_prompt:
        prompt = audio_prompt
        
    # Check Text Input
    chat_input_val = st.chat_input("Ask for fashion advice...")
    if chat_input_val:
        prompt = chat_input_val

    # Handle Uploaded File from Dialog
    uploaded_file = st.session_state.get("uploaded_file_temp", None)

    if prompt or (uploaded_file and prompt is None): 
        if uploaded_file and not prompt:
            prompt = "Analyze this outfit."
            
        if prompt:
            if st.session_state.msg_count >= 5 and not st.session_state.is_signed_in:
                sign_in_required_dialog()
            else:
                st.session_state.msg_count += 1
                st.session_state.stop_generating = False
                
                # 1. Construct User Message
                user_msg_content = prompt
                messages_payload = []
                
                if uploaded_file:
                    model = "meta-llama/llama-4-scout-17b-16e-instruct"
                    system_prompt = "Analyze the fabric, fit, and color of this outfit. Give specific advice on how to improve it."
                    
                    base64_image = encode_image(uploaded_file)
                    
                    user_message_struct = {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"{system_prompt}\n\nUser Question: {prompt}"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                },
                            },
                        ],
                    }
                    st.session_state.messages.append(user_message_struct)
                    messages_payload = [user_message_struct]
                    
                    st.session_state.uploaded_file_temp = None
                    
                    render_chat_message(st.session_state.messages[-1], len(st.session_state.messages)-1)
                        
                else:
                    model = "llama-3.3-70b-versatile"
                    
                    # 3. The 'Brain' (System Prompt Switch)
                    if st.session_state.gender_mode == "Men's Fashion":
                        system_prompt = "You are a Gentleman's Tailor. Focus on fit, structured fabrics (wool, linen), and classic menswear brands. Tone: Decisive, Classic."
                    else:
                        system_prompt = "You are a High-End Vogue Stylist. Focus on silhouettes, draping, diverse fabrics (silk, chiffon), and trending aesthetics. Tone: Chic, Empowering."
                    
                    if st.session_state.is_signed_in:
                        system_prompt += f" Address the user as {st.session_state.user_name}."
                    
                    # JSON Instruction for Language Detection
                    system_prompt += """
                    You are a helpful fashion assistant. You must always reply in the SAME language the user speaks to you.
                    
                    SHOPPING INSTRUCTION:
                    When you recommend specific clothing items (e.g., 'Maroon Kurta', 'Beige Chinos'), you must AUTOMATICALLY provide a buying link for them in the text.
                    Since you do not have a live inventory, you must construct a 'Smart Search Link' for Amazon India.
                    Format: `[Buy {Item Name}](https://www.amazon.in/s?k={Item+Name+with+pluses})`
                    Example: 'I recommend a [Maroon Kurta](https://www.amazon.in/s?k=maroon+kurta+men) paired with [Beige Chinos](https://www.amazon.in/s?k=beige+chinos+men).'
                    
                    CRITICAL: Your response must be a JSON object with three fields:
                    {
                        "response_text": "The actual fashion advice in the user's language (including the smart links)",
                        "detected_lang_code": "The 2-letter ISO code (e.g., en, ta, hi, fr)",
                        "speech_summary": "Generate a natural, conversational spoken version of your full advice. Do not artificially shorten it. You can speak as long as necessary to fully explain the styling concepts. Ensure the text is optimized for audio (remove markdown symbols like *, #, or - so the voice doesn't read them)."
                    }
                    """
                    
                    # Integrate Color Season
                    if st.session_state.user_season and isinstance(st.session_state.user_season, dict):
                        season_name = st.session_state.user_season.get('season', 'Unknown')
                        best_colors = st.session_state.user_season.get('best_colors', [])
                        system_prompt += f" The user's seasonal color palette is {season_name}. Suggest colors that flatter this season ({', '.join(best_colors)})."

                    # Integrate Wardrobe
                    if st.session_state.wardrobe:
                        # Filter items by current gender mode
                        current_mode = st.session_state.gender_mode
                        items_desc = []
                        for item in st.session_state.wardrobe:
                            item_gender = item.get('gender', "Men's Fashion") # Default to Men's
                            if item_gender == current_mode:
                                items_desc.append(f"{item['category']}")
                        
                        if items_desc:
                            system_prompt += f" You have access to the user's wardrobe: [{', '.join(items_desc)}]. ALWAYS prioritize recommending items from this list before suggesting new purchases. If you recommend an item from the wardrobe, explicitly say 'Wear your [Item Name]'."

                    # Integrate Planner (Schedule)
                    today = datetime.date.today()
                    plan_context = []
                    for i in range(1, 4): # Next 3 days
                        check_date = today + timedelta(days=i)
                        date_str = check_date.strftime("%Y-%m-%d")
                        plan = get_plan(date_str)
                        if plan:
                            # Resolve item names/categories
                            outfit_desc = []
                            for cat, item_id in plan.items():
                                # Find item in wardrobe to get details
                                found = next((it for it in st.session_state.wardrobe if it['id'] == item_id), None)
                                if found:
                                    outfit_desc.append(f"{cat}: {found.get('category', 'Item')}")
                            
                            if outfit_desc:
                                plan_context.append(f"{check_date.strftime('%A, %b %d')}: {', '.join(outfit_desc)}")
                    
                    if plan_context:
                        system_prompt += f" You know the user's schedule. Upcoming planned outfits: {'; '.join(plan_context)}. If they ask 'What am I wearing tomorrow?', check this schedule."

                    st.session_state.messages.append({"role": "user", "content": prompt})
                    render_chat_message(st.session_state.messages[-1], len(st.session_state.messages)-1)
                        
                    messages_payload = [{"role": "system", "content": system_prompt}]
                    for msg in st.session_state.messages[-10:]:
                        if isinstance(msg['content'], str):
                            # STRICTLY filter to only role and content to avoid API errors
                            clean_msg = {
                                "role": msg["role"],
                                "content": msg["content"]
                            }
                            messages_payload.append(clean_msg)

                # 2. Generate Response
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    with st.spinner('Outfyt AI is styling...'):
                        try:
                            # Call Groq API
                            completion = client.chat.completions.create(
                                model=model,
                                messages=messages_payload,
                                temperature=0.7,
                                max_tokens=4096,
                                stream=False,
                                response_format={"type": "json_object"}
                            )
                            
                            result_text = completion.choices[0].message.content
                            data = extract_json_from_text(result_text)
                            
                            response_text = data.get("response_text", result_text)
                            lang_code = data.get("detected_lang_code", "en")
                            speech_summary = data.get("speech_summary", "")
                            
                            # Display the text
                            message_placeholder.markdown(response_text)
                            
                            # Save to history
                            st.session_state.messages.append({"role": "assistant", "content": response_text})

                            # Use metadata IMMEDIATELY for TTS (Pre-generate)
                            if speech_summary:
                                try:
                                    # Cleanup old files
                                    audio_dir = "static/audio"
                                    if not os.path.exists(audio_dir):
                                        os.makedirs(audio_dir)
                                    
                                    # Determine config
                                    tld = "co.in" if lang_code in ['ta', 'hi', 'ml', 'kn', 'te'] else "com"
                                    
                                    unique_filename = f"audio_{uuid.uuid4()}.mp3"
                                    file_path = os.path.join(audio_dir, unique_filename)
                                    
                                    tts = gTTS(text=speech_summary, lang=lang_code, tld=tld)
                                    tts.save(file_path)
                                    
                                    # Cache it for the current message index
                                    msg_index = len(st.session_state.messages) - 1
                                    st.session_state.audio_cache[msg_index] = file_path
                                except Exception as e:
                                    # Fail silently for audio, text is already shown
                                    print(f"Audio generation failed: {e}")
                            
                            if audio_prompt:
                                st.session_state.audio_key += 1
                            
                            st.rerun()
                                
                        except Exception as e:
                            st.error(f"Error communicating with Groq: {e}")

# --- Main Interface ---
# Top Bar
# --- Main Interface ---
# Top Bar
col_logo, col_title = st.columns([0.7, 5])
with col_logo:
    st.image("assets/logo.png", width=110)
with col_title:
    if st.session_state.gender_mode == "Men's Fashion":
        st.markdown("# **Outfyt AI** | Gentleman's Companion")
    else:
        st.markdown("# **Outfyt AI** | Women's Fashion Director")

st.caption(f"High-End {st.session_state.gender_mode} Consultant (Powered by Groq)")

# --- Tabs ---
tab_chat, tab_color, tab_wardrobe, tab_planner = st.tabs(["💬 Chat", "🎨 Color Analysis", "🧥 My Wardrobe", "📅 Outfit Planner"])

# --- TAB 1: CHAT ---
with tab_chat:
    render_chat_interface()

# --- TAB 2: COLOR ANALYSIS ---
with tab_color:
    st.header("🎨 Personal Color Analysis")
    st.write("Upload a selfie to discover your seasonal color palette and find your power colors.")
    
    color_file = st.file_uploader("Upload a Selfie", type=["jpg", "jpeg", "png"], key="color_uploader")
    
    if color_file:
        st.image(color_file, width=300, caption="Your Selfie")
        
        if st.button("Find My Season", type="primary"):
            with st.spinner("Analyzing skin tone, eye color, and contrast..."):
                try:
                    base64_img = encode_image(color_file)
                    
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": '''You are a Master Color Analyst with expertise in the 12-Season Color System. 
                                    Analyze the skin tone (undertone), eye color, and hair contrast of the person in this photo. 
                                    Determine their specific Season (e.g., Deep Winter, Soft Autumn, Light Spring). 
                                    
                                    Return the result strictly as a JSON object with this structure:
                                    {
                                      "season_name": "Name of the Season Diagnosis",
                                      "reasoning": "A 2-sentence explanation of why this season was chosen based on their features.",
                                      "best_colors": [
                                         {"name": "Color Name 1", "hex": "#Hex1"},
                                         {"name": "Color Name 2", "hex": "#Hex2"},
                                         {"name": "Color Name 3", "hex": "#Hex3"},
                                         {"name": "Color Name 4", "hex": "#Hex4"},
                                         {"name": "Color Name 5", "hex": "#Hex5"}
                                      ],
                                      "avoid_colors": [
                                         {"name": "Bad Color 1", "hex": "#HexBad1"},
                                         {"name": "Bad Color 2", "hex": "#HexBad2"},
                                         {"name": "Bad Color 3", "hex": "#HexBad3"}
                                      ]
                                    }'''},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_img}",
                                        },
                                    },
                                ],
                            }
                        ],
                        temperature=0.5,
                        max_tokens=1000,
                        response_format={"type": "json_object"}
                    )
                    
                    result_text = response.choices[0].message.content
                    analysis = extract_json_from_text(result_text)
                    
                    if analysis:
                        st.session_state.user_season = analysis
                        st.rerun()
                    else:
                        st.error("Could not parse the analysis result. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error during analysis: {e}")

    if st.session_state.user_season:
        season_data = st.session_state.user_season
        
        st.divider()
        st.markdown(f'<div class="season-title">You are a {season_data.get("season_name", "Unknown Season")}</div>', unsafe_allow_html=True)
        st.write(f"**Reasoning:** {season_data.get('reasoning', '')}")
        
        st.subheader("✅ Your Power Colors")
        display_color_swatches(season_data.get("best_colors", []))
        
        st.subheader("❌ Colors to Avoid")
        display_color_swatches(season_data.get("avoid_colors", []))

# --- TAB 3: MY WARDROBE ---
with tab_wardrobe:
    st.header("🧥 My Digital Wardrobe")
    st.write(f"Catalog your **{st.session_state.gender_mode}** items.")
    
    col_add, col_gallery = st.columns([1, 2])
    
    # 4. Wardrobe Logic (The Split)
    MENS_CATEGORIES = ['Suit', 'Blazer', 'Shirt', 'T-Shirt', 'Trousers', 'Jeans', 'Shoes', 'Accessory']
    WOMENS_CATEGORIES = ['Dress', 'Saree', 'Lehenga', 'Top', 'Skirt', 'Jeans', 'Trousers', 'Heels', 'Accessory']
    
    current_categories = MENS_CATEGORIES if st.session_state.gender_mode == "Men's Fashion" else WOMENS_CATEGORIES
    
    with col_add:
        st.subheader("Add New Item")
        wardrobe_file = st.file_uploader("Upload Cloth Image", type=["jpg", "jpeg", "png"], key="wardrobe_uploader")
        category = st.selectbox("Category", current_categories)
        
        if st.button("Add to Closet", type="primary"):
            if wardrobe_file:
                # Pass current gender mode to save function
                if save_item_to_wardrobe(wardrobe_file, category, st.session_state.gender_mode):
                    st.success("Item added to wardrobe!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Please upload an image first.")
                
    with col_gallery:
        st.subheader("Your Closet")
        st.subheader("Your Closet")
        # FORCE REFRESH: Ensure wardrobe is fetched for the current mode
        # Use user_id from session state, default to 1 if not set
        current_user_id = st.session_state.get("user_id", 1)
        # FORCE REFRESH: Ensure wardrobe is fetched for the current mode
        # Use user_id from session state, default to 1 if not set
        current_user_id = st.session_state.get("user_id", 1)
        
        # 1. Fetch EVERYTHING (One call, correct argument)
        items_list = get_wardrobe_items(current_user_id)
        
        # Convert to DataFrame for easier filtering (as requested)
        if items_list:
            all_items = pd.DataFrame(items_list)
        else:
            all_items = pd.DataFrame()

        # 2. Filter Client-Side (Python) based on the Sidebar Toggle
        if not all_items.empty:
            # Filter by the 'gender' column
            # Ensure exact string matching with your toggle values ("Men's Fashion", "Women's Fashion")
            current_mode = st.session_state.gender_mode
            
            # Handle case where 'gender' column might be missing in some rows (though unlikely with DB)
            if 'gender' in all_items.columns:
                filtered_items = all_items[all_items['gender'] == current_mode]
            else:
                filtered_items = pd.DataFrame()

            if filtered_items.empty:
                st.info(f"No items found for {current_mode}.")
            else:
                # 3. Group by Category and Display
                # Get unique categories present in the FILTERED list
                categories_found = filtered_items['category'].unique()

                for category in categories_found:
                    st.markdown(f"### {category}") # Section Header (e.g., "Suit")
                    
                    # Get items for just this category
                    cat_items = filtered_items[filtered_items['category'] == category]
                    
                    # Display in a grid
                    cols = st.columns(3)
                    for i, (index, row) in enumerate(cat_items.iterrows()):
                        with cols[i % 3]:
                            # Display Image
                            if os.path.exists(row['image_path']):
                                st.markdown(f"""
                                <div class="wardrobe-item">
                                    <img src="data:image/jpeg;base64,{base64.b64encode(open(row['image_path'], "rb").read()).decode()}" style="width:100%; border-radius:10px;">
                                    <div class="wardrobe-caption">{row['category']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Remove Button
                                if st.button(f"🗑️ Remove", key=f"del_{row['id']}"):
                                    delete_item_from_wardrobe(row['id'])
                                    st.rerun()
                            else:
                                st.error(f"Image not found")
                                if st.button("🗑️ Remove Broken", key=f"del_broken_{row['id']}"):
                                    delete_item_from_wardrobe(row['id'])
                                    st.rerun()
        else:
            st.info("Your wardrobe is empty. Upload some items to get started!")

    st.divider()
    if st.button("✅ Finished Updating Wardrobe", use_container_width=True):
        st.success("Wardrobe updated successfully! Now you can ask Outfyt AI to create outfits with your clothes.")

# --- TAB 4: OUTFIT PLANNER ---
with tab_planner:
    st.header("📅 Outfit Planner")
    st.write("Schedule your looks for the week ahead.")
    
    col_scheduler, col_week = st.columns([1, 2])
    
    with col_scheduler:
        st.subheader("✨ Smart Planner")
        
        with st.form("smart_planner_form"):
            occasion = st.selectbox("Occasion", ["Office/Work", "Party/Night", "Vacation", "Casual/Weekend"])
            num_days = st.slider("Days to Plan", 1, 7, 5)
            st.caption("Plan starts from tomorrow.")
            
            c_gen, c_clear = st.columns([2, 1])
            with c_gen:
                if st.form_submit_button("✨ Generate Plan", type="primary", use_container_width=True):
                    with st.spinner("AI is styling your week..."):
                        success, msg = generate_smart_plan(occasion, num_days)
                        if success:
                            st.success(f"Plan generated for {occasion}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed: {msg}")
            with c_clear:
                if st.form_submit_button("🗑️ Clear All", type="secondary", use_container_width=True):
                    clear_all_plans()
                    st.rerun()
        
        st.divider()
        st.caption("Manual Override")
        with st.expander("Manually Plan a Day"):
            # Session State Fix: Ensure stored date is not in the past
            today = datetime.date.today()
            if "manual_date" in st.session_state:
                if st.session_state.manual_date < today:
                    st.session_state.manual_date = today

            plan_date = st.date_input("Select Date", min_value=today, key="manual_date")
            date_str = plan_date.strftime("%Y-%m-%d")
            
            # Dynamic Dropdowns based on Gender Mode
            current_mode = st.session_state.gender_mode
            
            if current_mode == "Men's Fashion":
                cats_to_plan = ["Suit", "Shirt", "Trousers", "Shoes"]
            else:
                cats_to_plan = ["Dress", "Top", "Skirt", "Trousers", "Heels"]
                
            selected_outfit = {}
            
            with st.form("manual_planner_form"):
                # 1. Fetch ALL items for this user (Fixing TypeError at 1812)
                current_user_id = st.session_state.get("user_id", 1)
                all_items_list = get_wardrobe_items(current_user_id)
                all_items_df = pd.DataFrame(all_items_list) if all_items_list else pd.DataFrame()

                for cat in cats_to_plan:
                    # 2. Filter Client-Side
                    items = []
                    if not all_items_df.empty and 'gender' in all_items_df.columns and 'category' in all_items_df.columns:
                        # Filter for current mode AND current category
                        mask = (all_items_df['gender'] == current_mode) & (all_items_df['category'] == cat)
                        items = all_items_df[mask].to_dict('records')

                    options = {item['id']: f"{item['category']} (Added {datetime.datetime.fromtimestamp(item['added_at']).strftime('%m/%d')})" for item in items}
                    
                    selected_id = st.selectbox(f"Select {cat}", options=list(options.keys()), format_func=lambda x: options[x], key=f"plan_{cat}", index=None, placeholder="Choose an item...")
                    if selected_id:
                        selected_outfit[cat] = selected_id
                
                if st.form_submit_button("Save Manual Look"):
                    if selected_outfit:
                        if save_plan(date_str, selected_outfit):
                            st.success(f"Outfit saved for {plan_date.strftime('%A, %b %d')}!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("Please select at least one item.")

    with col_week:
        st.subheader("Your Week Ahead")
        
        today = datetime.date.today()
        for i in range(5):
            day = today + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_display = day.strftime("%A, %b %d")
            
            plan = get_plan(day_str)
            
            # Gender Leakage Fix: Skip plans not for current mode
            if plan and plan.get('gender') != st.session_state.gender_mode:
                plan = None

            st.markdown(f"**{day_display}**")
            
            if plan:
                # Card Style
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1);">
                    <h4 style="margin-top:0;">{day_display}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Filter out 'gender' and 'note' keys from display loop
                display_items = {k: v for k, v in plan.items() if k not in ['gender', 'note']}
                cols = st.columns(len(display_items))
                idx = 0
                for cat, item_id in display_items.items():
                    item = next((it for it in st.session_state.wardrobe if it['id'] == item_id), None)
                    if item and os.path.exists(item['image_path']):
                        with cols[idx]:
                            st.image(item['image_path'], caption=cat, use_container_width=True)
                        idx += 1
                
                # Style Note
                if 'note' in plan:
                    st.info(f"💡 **Style Note:** {plan['note']}")
                
                # Actions
                c_shuf, c_dl, c_rem = st.columns([1, 1, 1])
                with c_shuf:
                    if st.button("🔄 Shuffle", key=f"shuf_{day_str}", use_container_width=True):
                        with st.spinner("Mixing it up..."):
                            shuffle_day_plan(day_str, "Casual") 
                            st.rerun()
                            
                with c_dl:
                    if st.button("🎨 Customize Story", key=f"cust_{day_str}", use_container_width=True):
                        story_studio_dialog(plan, day_display)
                
                with c_rem:
                    if st.button("❌ Remove", key=f"rem_{day_str}", use_container_width=True):
                        delete_plan_day(day_str)
                        st.rerun()
                
                st.markdown("---")
            else:
                st.markdown(f"<div style='padding:10px; background:rgba(255,255,255,0.05); border-radius:10px; color:#888; margin-bottom:10px;'>No outfit planned</div>", unsafe_allow_html=True)
