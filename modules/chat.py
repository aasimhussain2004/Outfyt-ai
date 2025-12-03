import streamlit as st
import base64
import os
import time
import uuid
import datetime
from datetime import timedelta
import json
import re
import io
from groq import Groq
from gtts import gTTS
from modules.auth import sign_in_required_dialog
from modules.wardrobe import get_wardrobe_items
from modules.planner import get_plan

# Initialize Groq Client
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    client = None

@st.dialog("Upload Outfit Photo")
def upload_dialog():
    st.write("Upload a photo for analysis.")
    uploaded = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    if uploaded:
        st.session_state.uploaded_file_temp = uploaded
        if st.button("Analyze", type="primary"):
            st.session_state.show_upload_dialog = False
            st.rerun()

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

@st.fragment
def handle_chat():
    # --- 1. Display History First (Top) ---
    for i, message in enumerate(st.session_state.messages):
        # Determine Avatar
        if message["role"] == "assistant":
            avatar_icon = "assets/logo.png" if os.path.exists("assets/logo.png") else "🤖"
        else:
            user_name = st.session_state.get("user_name", "User")
            avatar_icon = f"https://ui-avatars.com/api/?name={user_name}&background=C5B358&color=1a1a2e" if user_name != "User" else "👤"

        with st.chat_message(message["role"], avatar=avatar_icon):
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            elif isinstance(message["content"], list):
                for part in message["content"]:
                    if part['type'] == 'text':
                        st.markdown(part['text'])

    # --- 2. Action Buttons (Middle) ---
    c1, c2, c3 = st.columns([1, 10, 1])
    with c1:
        if st.button("📷", key="btn_upload_main", help="Analyze an Outfit"):
            upload_dialog()
    with c3:
        if st.button("🎤", key="btn_voice_main", help="Toggle Voice Mode"):
            st.session_state.show_voice_ui = not st.session_state.show_voice_ui
            st.rerun()

    # Voice UI Input
    audio_prompt = None
    if st.session_state.show_voice_ui:
        st.markdown("### 🎙️ Voice Mode")
        audio_input = st.audio_input("Speak now...", key=f"audio_{st.session_state.audio_key}")
        if audio_input:
            with st.spinner("Listening..."):
                transcribed_text = transcribe_audio(audio_input)
                if transcribed_text:
                    audio_prompt = transcribed_text

    # --- 3. Input Logic (Bottom) ---
    # Check for Voice Prompt OR Text Input
    prompt = st.chat_input("Ask for fashion advice...")
    
    if audio_prompt:
        prompt = audio_prompt

    # Handle Uploaded File
    uploaded_file = st.session_state.get("uploaded_file_temp", None)

    if prompt or (uploaded_file and prompt is None):
        if uploaded_file and not prompt:
            prompt = "Analyze this outfit."

        if prompt:
            # --- 1. GUEST LIMIT CHECK (The Hook) ---
            if not st.session_state.get("is_signed_in", False):
                guest_count = st.session_state.get("guest_msg_count", 0)
                if guest_count >= 2:
                    st.warning("⚠️ You've reached the guest limit (2 messages).")
                    st.info("Sign In to continue chatting and save your wardrobe.")
                    
                    def trigger_signin():
                        st.session_state.temp_signin = True
                        
                    st.button("Sign In Now", key="guest_limit_signin", on_click=trigger_signin)
                    
                    if st.session_state.get("temp_signin"):
                        st.rerun()
                    st.stop()

            # --- 2. FREEMIUM CHECK (Signed In Users) ---
            from modules import subscription, database
            user_id = st.session_state.get("user_id", 1)
            
            # Only check DB limit if signed in (Guests are handled above)
            if st.session_state.get("is_signed_in", False):
                is_allowed, message = subscription.check_message_limit(database.supabase, user_id)
                
                if not is_allowed:
                    st.error(f"⚠️ {message}")
                    if st.button("🚀 Upgrade to Premium", key="limit_upgrade_btn"):
                        st.session_state.trigger_upgrade = True
                        st.rerun()
                    st.stop()
            # ----------------------

            st.session_state.stop_generating = False

            # A. Display User Message Immediately
            user_name = st.session_state.get("user_name", "User")
            user_avatar = f"https://ui-avatars.com/api/?name={user_name}&background=C5B358&color=1a1a2e" if user_name != "User" else "👤"
            
            with st.chat_message("user", avatar=user_avatar):
                st.markdown(prompt)

            # B. Append User Message
            # Construct Message Payload
            if uploaded_file:
                base64_image = encode_image(uploaded_file)
                user_msg_struct = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Analyze this outfit. User Question: {prompt}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
                st.session_state.uploaded_file_temp = None
            else:
                user_msg_struct = {"role": "user", "content": prompt}
                
                st.session_state.messages.append(user_msg_struct)

                # C. AI Response
                with st.chat_message("assistant", avatar="assets/logo.png"):
                    with st.spinner("Outfyt AI is styling..."):
                        try:
                            # 1. Build Context (Silent)
                            messages_payload = []
                            
                            # Get System Prompt
                            system_prompt = get_system_prompt(
                                st.session_state.gender_mode,
                                st.session_state.is_signed_in,
                                st.session_state.get("user_name"),
                                st.session_state.wardrobe
                            )
                            
                            # Add System Prompt
                            messages_payload.append({"role": "system", "content": system_prompt})

                            # Add History (Last 10)
                            for msg in st.session_state.messages[-10:]:
                                if isinstance(msg['content'], str):
                                    messages_payload.append({"role": msg["role"], "content": msg["content"]})
                                elif isinstance(msg['content'], list):
                                    messages_payload.append(msg)

                            # 2. Call LLM
                            model = "llama-3.3-70b-versatile"
                            if uploaded_file:
                                model = "meta-llama/llama-4-scout-17b-16e-instruct" # Vision model

                            response_text = get_ai_response(messages_payload, model)
                            
                            # 3. Display Response
                            st.markdown(response_text)
                            
                            # 4. Append AI Response
                            st.session_state.messages.append({"role": "assistant", "content": response_text})
                            
                            # 5. Rerun to Lock
                            # Increment DB Count (If signed in)
                            if st.session_state.get("is_signed_in", False):
                                subscription.increment_message_count(user_id)
                            else:
                                # Increment Guest Count
                                st.session_state.guest_msg_count += 1
                            
                            if audio_prompt:
                                st.session_state.audio_key += 1
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")

def get_system_prompt(gender_mode, is_signed_in, user_name, wardrobe_items):
    if gender_mode == "Men's Fashion":
        system_prompt = """
        You are Outfyt, a high-end Gentleman's Style Consultant. Your tone is authoritative, concise, and focused on timeless masculinity. Focus on Fit, Fabric, and Context.
        Rules:
        1. Never suggest a Navy Jacket with Black Trousers.
        2. A "Suit" implies matching jacket and trousers.
        3. If the user input is short (e.g., "Hi"), ask for the occasion.
        4. Output outfits in Bullet Points.
        """
    else:
        system_prompt = """
        You are Outfyt, a top-tier Women's Fashion Director. Your tone is warm, empowering, and trend-aware. Focus on Body Shape (Hourglass, Pear, etc.) and Color Theory.
        Rules:
        1. Ask about the user's "Season" (Winter/Summer) if relevant.
        2. Focus on silhouettes and proportions.
        3. If the user input is short, ask: "Are we dressing for work, a date, or a party?"
        4. Output outfits in Bullet Points.
        """
    
    system_prompt += " Always use Markdown (bolding key items) for readability."

    if is_signed_in:
        system_prompt += f" Address the user as {user_name}."

    # Wardrobe Context
    if wardrobe_items:
        current_mode = gender_mode
        items_desc = [f"{item['category']}" for item in wardrobe_items if item.get('gender', "Men's Fashion") == current_mode]
        if items_desc:
            system_prompt += f" You have access to the user's wardrobe: [{', '.join(items_desc)}]. ALWAYS prioritize recommending items from this list."

    # Planner Context
    today = datetime.date.today()
    plan_context = []
    for i in range(1, 4):
        check_date = today + timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        plan = get_plan(date_str)
        if plan:
            plan_context.append(f"{check_date.strftime('%A')}: {plan.get('note', 'Outfit planned')}")
    if plan_context:
        system_prompt += f" Upcoming schedule: {'; '.join(plan_context)}."
        
    return system_prompt

def get_ai_response(messages, model="llama-3.3-70b-versatile"):
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"


