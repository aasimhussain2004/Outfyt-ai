import streamlit as st
import uuid

from modules import database

def init_user_session():
    """Initialize session state and render sidebar auth/mode UI."""
    
    # 0. Check for Persistent Login (Query Params)
    if "user_id" in st.query_params:
        qp_user_id = st.query_params["user_id"]
        # Validate UUID format roughly
        if len(qp_user_id) > 20: 
            st.session_state.user_id = qp_user_id
            st.session_state.is_signed_in = True
            
            # Fetch User Name if not set
            if "user_name" not in st.session_state:
                try:
                    response = database.supabase.table("user_profiles").select("name").eq("user_id", st.session_state.user_id).execute()
                    if response.data:
                        st.session_state.user_name = response.data[0].get("name", "User")
                except:
                    st.session_state.user_name = "User"

    # Session State Initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "stop_generating" not in st.session_state:
        st.session_state.stop_generating = False
    if "msg_count" not in st.session_state:
        st.session_state.msg_count = 0
    if "guest_msg_count" not in st.session_state:
        st.session_state.guest_msg_count = 0
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

    # Sidebar
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
                # Clear Query Params
                st.query_params.clear()
                # Generate new temp ID
                st.session_state.user_id = str(uuid.uuid4())
                st.rerun()
        else:
            if st.button("Sign In", use_container_width=True):
                st.session_state.temp_signin = True
                st.rerun()

    # Handle Dialogs
    if st.session_state.get("temp_signin"):
        sign_in_dialog_func()

    # Persistent User ID for Session (Fallback)
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
        
    return st.session_state.user_id

@st.dialog("Sign In")
def sign_in_dialog_func():
    st.write("Enter your Name to complete Sign In:")
    st.caption("This will save your data permanently.")
    name = st.text_input("Name")
    if name:
        if st.button("Confirm"):
            # 1. Check if user exists in DB
            try:
                response = database.supabase.table("user_profiles").select("*").eq("name", name).execute()
                
                if response.data:
                    # User Exists - Load Data
                    user_data = response.data[0]
                    st.session_state.user_id = user_data['user_id']
                    st.session_state.user_name = user_data['name']
                    st.toast(f"Welcome back, {name}!", icon="👋")
                else:
                    # New User - Create in DB
                    new_id = str(uuid.uuid4())
                    database.supabase.table("user_profiles").insert({
                        "user_id": new_id,
                        "name": name,
                        "is_premium": False
                    }).execute()
                    st.session_state.user_id = new_id
                    st.session_state.user_name = name
                    st.toast(f"Account created for {name}!", icon="🎉")
                
                # 2. Update Session & Query Params
                st.session_state.is_signed_in = True
                st.session_state.temp_signin = False
                st.query_params["user_id"] = st.session_state.user_id
                st.rerun()
                
            except Exception as e:
                st.error(f"Sign in failed: {e}")

@st.dialog("Sign In Required")
def sign_in_required_dialog():
    st.write("You've reached the free limit of 5 messages.")
    st.write("Sign in to continue chatting with Outfyt AI.")
    if st.button("Continue with Google", use_container_width=True):
        st.session_state.temp_signin = True
        st.rerun()
