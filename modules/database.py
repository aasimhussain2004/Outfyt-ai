import streamlit as st
from supabase import create_client, ClientOptions

# --- Custom Storage for Streamlit ---
# Using a global dictionary to persist data across re-runs within the same process.
# This is necessary because st.session_state can be cleared on external redirects.
_LOCAL_STORAGE = {}

class StreamlitStorage:
    """
    Custom storage implementation for Supabase-py using a global in-memory dictionary.
    This ensures the PKCE code_verifier persists even if the Streamlit session is reset.
    """
    def get_item(self, key: str) -> str | None:
        return _LOCAL_STORAGE.get(key, None)

    def set_item(self, key: str, value: str) -> None:
        _LOCAL_STORAGE[key] = value

    def remove_item(self, key: str) -> None:
        if key in _LOCAL_STORAGE:
            del _LOCAL_STORAGE[key]

# Initialize Supabase Client with Custom Storage
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    options = ClientOptions(
        auto_refresh_token=True,
        persist_session=True,
        storage=StreamlitStorage()
    )
    
    supabase = create_client(url, key, options=options)
except Exception as e:
    # st.error(f"Supabase connection failed: {e}") 
    supabase = None

def get_user_profile(user_id):
    """
    Fetch user profile data from Supabase 'user_profiles' table.
    Returns a dict with 'is_premium' status, or default if not found.
    """
    if not supabase:
        return {"is_premium": False}
        
    try:
        # Assuming table name is 'user_profiles' as requested
        # If it doesn't exist, we might need to fallback or handle error
        response = supabase.table("user_profiles").select("is_premium").eq("user_id", str(user_id)).execute()
        
        if response.data:
            return response.data[0]
        else:
            return {"is_premium": False}
    except Exception:
        return {"is_premium": False}

def upsert_user(user_id, email, full_name):
    """
    Upsert user details into 'user_profiles' table.
    Updates last_active if user exists, or creates new record.
    """
    if not supabase:
        return False
        
    try:
        data = {
            "user_id": str(user_id),
            "email": email,
            "name": full_name,
            "last_active": "now()" # Re-enabled: Column exists now
        }
        
        # Upsert (Insert or Update)
        supabase.table("user_profiles").upsert(data).execute()
        return True
    except Exception as e:
        # Show warning to user so they know to fix the DB
        st.warning(f"⚠️ Profile Sync Failed: Ensure 'email' and 'last_active' columns exist in 'user_profiles' table. Error: {e}")
        return False
