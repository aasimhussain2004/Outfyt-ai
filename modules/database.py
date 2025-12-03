import streamlit as st
from sqlalchemy import text
from supabase import create_client

# Initialize Supabase Client
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    # st.error(f"Supabase connection failed: {e}") # Avoid error on import if secrets missing during build
    supabase = None

@st.cache_resource
def init_db():
    """Initialize the database tables."""
    conn = st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
    with conn.session as s:
        s.execute(text('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS wardrobe 
                     (id TEXT PRIMARY KEY, user_id TEXT, category TEXT, gender TEXT, image_path TEXT, filename TEXT, added_at FLOAT)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS planner 
                     (date TEXT PRIMARY KEY, user_id TEXT, outfit_data TEXT)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS chat_history 
                     (id INTEGER PRIMARY KEY, user_id TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)'''))
        s.execute(text("INSERT INTO users (id, username) VALUES (1, 'default_user') ON CONFLICT (id) DO NOTHING"))
        
        # Add tutorial_completed column if it doesn't exist
        try:
            s.execute(text("ALTER TABLE users ADD COLUMN tutorial_completed BOOLEAN DEFAULT FALSE"))
        except Exception:
            pass # Column likely already exists
            
        # Schema Migration: Ensure user_id is TEXT (for UUID support)
        try:
            # SQLite syntax for altering column type is limited, but Supabase (Postgres) supports it.
            # However, if using SQLite locally, we might need a different approach.
            # Assuming Supabase (Postgres) based on connection string.
            s.execute(text("ALTER TABLE wardrobe ALTER COLUMN user_id TYPE TEXT"))
            s.execute(text("ALTER TABLE planner ALTER COLUMN user_id TYPE TEXT"))
        except Exception as e:
            # Ignore if already TEXT or other error (e.g. SQLite limitation)
            pass
            
        s.commit()

def get_connection():
    """Return the SQLAlchemy connection object."""
    return st.connection("supabase", type="sql", url=st.secrets["SUPABASE_DB_URL"])
