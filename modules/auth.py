import streamlit as st
import uuid
import json
import time
from modules import database

# --- HELPER FUNCTIONS ---

def get_current_user():
    """
    Returns (user_id, user_email, user_name) if logged in, else (None, None, None).
    Checks Session State first, then Supabase Session.
    """
    # 1. Check Session State
    if st.session_state.get("is_signed_in"):
        return (
            st.session_state.user_id,
            st.session_state.user_email,
            st.session_state.user_name,
        )

    # 2. Check Supabase Session (Persistence)
    try:
        # supabase.auth.get_session() returns a RESPONSE object, not the raw session
        # With the new client options, this should automatically refresh if needed
        resp = database.supabase.auth.get_session()
        
        # In the new client, the session is in resp.session (or resp might be the session itself depending on version)
        # Safest way is to check for 'user' attribute on whatever we get back
        
        user = None
        if hasattr(resp, "user") and resp.user:
            user = resp.user
        elif hasattr(resp, "session") and resp.session and resp.session.user:
             user = resp.session.user
        
        if user:
            uid, email, name = _update_session_state(user)
            # Sync User to DB on restore (in case it failed during login)
            database.upsert_user(uid, email, name)
            return uid, email, name
            
    except Exception:
        # swallow and treat as not logged in
        pass

    return None, None, None


def _update_session_state(user):
    """Internal helper to update session state from a User object."""
    st.session_state.is_signed_in = True
    st.session_state.user_id = user.id
    st.session_state.user_email = user.email

    # Robust Metadata Extraction
    meta = getattr(user, "user_metadata", {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}

    # Handle Dict access safely
    if isinstance(meta, dict):
        name = meta.get("full_name") or meta.get("name") or user.email
    else:
        name = user.email

    st.session_state.user_name = name
    return user.id, user.email, name


def handle_oauth_callback():
    """Checks for OAuth code in URL and exchanges it for a session."""
    if "code" not in st.query_params:
        return  # no callback, nothing to do

    code = st.query_params["code"]

    try:
        # Supabase Python expects a dict with "auth_code"
        # The PKCE code_verifier is now automatically handled by the client storage
        res = database.supabase.auth.exchange_code_for_session(
            {"auth_code": code}
        )

        # ---- handle result safely ----
        user = None
        if hasattr(res, "user") and res.user:
            user = res.user
        elif isinstance(res, dict) and "user" in res:
            user = res["user"]
        elif hasattr(res, "session") and res.session and res.session.user:
            user = res.session.user

        if not user:
            st.error("Login failed: no user data returned from Supabase.")
            if st.button("Retry"):
                st.query_params.clear()
                st.rerun()
            return

        uid, email, name = _update_session_state(user)
        
        # Sync User to DB (Ensure profile exists)
        database.upsert_user(uid, email, name)
        
        st.toast("Login successful! 🎉", icon="🎉")
        st.query_params.clear()
        st.rerun()

    except Exception as e:
        # Only runs if Supabase throws an error (like the PKCE one)
        st.error(f"Google Login Failed: {e}")
        if st.button("Clear Error"):
            st.query_params.clear()
            st.rerun()





def login_button():
    """Renders the Login Button."""
    if st.button("Continue with Google", type="primary", use_container_width=True):
        try:
            # Get OAuth URL
            # Use 'redirect_to' in options (snake_case)
            data = database.supabase.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {
                        "redirect_to": "http://localhost:8501",
                    },
                }
            )

            # PKCE code_verifier is now automatically handled by StreamlitStorage in database.py
            # No need to manually extract and save it here.

            # Handle URL (Object or Dict)
            url = None
            if hasattr(data, "url"):
                url = data.url
            elif isinstance(data, dict):
                url = data.get("url")

            if url:
                st.link_button(
                    "👉 Click to Sign In",
                    url,
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.error("Could not generate login link.")

        except Exception as e:
            st.error(f"Auth Error: {e}")

            # Handle URL (Object or Dict)
            url = None
            if hasattr(data, "url"):
                url = data.url
            elif isinstance(data, dict):
                url = data.get("url")

            if url:
                st.link_button(
                    "👉 Click to Sign In",
                    url,
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.error("Could not generate login link.")

        except Exception as e:
            st.error(f"Auth Error: {e}")



def logout():
    """Signs out the user and clears session."""
    try:
        database.supabase.auth.sign_out()
    except Exception:
        # If sign_out fails (network, etc.), still clear local session
        pass

    st.session_state.is_signed_in = False
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.user_id = str(uuid.uuid4())  # Reset to Guest ID
    st.rerun()


# --- MAIN INIT FUNCTION ---


def init_user_session():
    """Initialize session state and render sidebar auth/mode UI."""

    # 1. Handle Callback (Priority)
    handle_oauth_callback()

    # 2. Initialize Defaults
    defaults = {
        "messages": [],
        "chat_history": [],
        "stop_generating": False,
        "msg_count": 0,
        "guest_msg_count": 0,
        "user_name": None,
        "is_signed_in": False,
        "last_audio_input": None,
        "audio_key": 0,
        "audio_cache": {},
        "playing_audio_id": None,
        "user_season": None,
        "wardrobe": [],
        "planner": {},
        "show_voice_ui": False,
        "show_upload_dialog": False,
        "gender_mode": "Men's Fashion",
        "prev_mode": "Men's Fashion",
        "shopping_results": {},
        "language": "English (US)",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 3. Check Persistence (If not signed in via callback)
    if not st.session_state.is_signed_in:
        get_current_user()

    # Persistent User ID (Fallback)
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())

    # 4. Sidebar UI
    with st.sidebar:
        col_logo, col_title = st.columns([2, 3])
        with col_logo:
            st.image("assets/logo.png", width=180)
        with col_title:
            st.markdown(
                "<h3 style='margin-top: 20px; margin-bottom: 10; font-size: 22px;'>Style Companion</h3>",
                unsafe_allow_html=True,
            )

        # Mode Toggle
        mode = st.radio(
            "Mode",
            ["Men's Fashion", "Women's Fashion"],
            horizontal=True,
            key="gender_mode_radio",
        )
        st.session_state.gender_mode = mode

        # Mode Notification
        if st.session_state.gender_mode != st.session_state.prev_mode:
            if st.session_state.gender_mode == "Women's Fashion":
                st.toast("Activating Women's Style Mode... 💃", icon="✨")
            else:
                st.toast("Activating Gentleman's Mode... 👔", icon="🎩")
            st.session_state.prev_mode = st.session_state.gender_mode

        # New Chat Button
        if st.button("✨ New Chat", use_container_width=True, type="primary"):
            if st.session_state.messages:
                st.session_state.chat_history.append(st.session_state.messages)
            st.session_state.messages = []
            st.session_state.msg_count = 0
            st.session_state.audio_cache = {}
            st.session_state.playing_audio_id = None
            st.session_state.shopping_results = {}
            st.rerun()

        # History
        st.subheader("History")
        if not st.session_state.chat_history:
            st.caption("No recent chats.")
        else:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                title = "New Chat"
                for msg in chat:
                    if msg["role"] == "user":
                        title = msg["content"][:20] + "..."
                        break
                if st.button(title, key=f"hist_{i}", use_container_width=True):
                    st.session_state.messages = chat
                    st.rerun()

        st.divider()

        # Auth Buttons
        if st.session_state.is_signed_in:
            st.write(f"**{st.session_state.user_name}**")
            if st.button("Sign Out", use_container_width=True):
                logout()
        else:
            if "code" not in st.query_params:
                if st.button("Sign In", use_container_width=True):
                    st.session_state.temp_signin = True
                    st.rerun()

    # Handle Dialogs
    if st.session_state.get("temp_signin") and "code" not in st.query_params:
        sign_in_dialog_func()

    return st.session_state.user_id


@st.dialog("Sign In")
def sign_in_dialog_func():
    st.write("Sign in to save your wardrobe and chats.")
    login_button()


@st.dialog("Sign In Required")
def sign_in_required_dialog():
    st.write("You've reached the free limit of 5 messages.")
    st.write("Sign in to continue chatting with Outfyt AI.")
    login_button()
