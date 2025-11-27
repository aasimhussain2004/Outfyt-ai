import pytest
import sqlite3
import sys
import os
from unittest.mock import MagicMock, patch

# Fixture to mock Streamlit and import app.py
@pytest.fixture(scope="module")
def app_module():
    """
    Mocks Streamlit and imports the app module.
    This allows testing functions in app.py without running the Streamlit script.
    """
    with patch.dict(sys.modules):
        # Add project root to sys.path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        mock_st = MagicMock()
        mock_st.secrets = {"GROQ_API_KEY": "fake_key"}
        # Custom SessionState to support both dict and attribute access
        class SessionState(dict):
            def __getattr__(self, item):
                return self.get(item)
            def __setattr__(self, key, value):
                self[key] = value
        
        mock_st.session_state = SessionState({
            "wardrobe": [],
            "planner": {},
            "gender_mode": "Men's Fashion",
            "messages": [],
            "user_name": "Test User",
            "is_signed_in": True,
            "shopping_results": {},
            "audio_cache": {},
            "playing_audio_id": None
        })
        # Mock context managers
        mock_st.sidebar.__enter__.return_value = None
        mock_st.sidebar.__exit__.return_value = None
        
        def mock_columns(spec):
            if isinstance(spec, int):
                count = spec
            else:
                count = len(spec)
            return [MagicMock() for _ in range(count)]
        
        mock_st.columns.side_effect = mock_columns
        
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_st.spinner.return_value.__enter__.return_value = None
        mock_st.spinner.return_value.__exit__.return_value = None
        
        sys.modules["streamlit"] = mock_st
        
        # Patch sqlite3.connect BEFORE import to prevent init_db from creating a file
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            import app
            return app

@pytest.fixture
def mock_db(app_module):
    """
    Sets up a temporary in-memory SQLite DB and patches sqlite3.connect
    to return a connection to it.
    """
    # Create a shared in-memory DB
    # We use a shared cache so multiple connections see the same DB
    conn = sqlite3.connect("file::memory:?cache=shared", uri=True)
    c = conn.cursor()
    
    # Initialize Schema
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wardrobe 
                 (id TEXT PRIMARY KEY, user_id INTEGER, category TEXT, gender TEXT, image_path TEXT, filename TEXT, added_at REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS planner 
                 (date TEXT PRIMARY KEY, user_id INTEGER, outfit_data TEXT)''')
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'default_user')")
    conn.commit()
    
    # Patch sqlite3.connect to return a NEW connection to the SAME shared in-memory DB
    # We also need to ensure close() doesn't actually destroy the DB if we want to inspect it,
    # but for shared memory DB, closing one connection doesn't destroy it if others are open?
    # Actually, with shared cache, it persists as long as one connection is open.
    # So we keep 'conn' open in this fixture.
    
    def custom_connect(*args, **kwargs):
        return sqlite3.connect("file::memory:?cache=shared", uri=True)
        
    with patch("sqlite3.connect", side_effect=custom_connect):
        yield conn
    
    conn.close()

@pytest.fixture
def mock_groq():
    with patch("app.Groq") as MockGroq:
        client = MockGroq.return_value
        yield client
