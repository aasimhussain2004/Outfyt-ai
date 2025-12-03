import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Streamlit secrets before importing modules
import streamlit as st
if not hasattr(st, "secrets"):
    st.secrets = {
        "SUPABASE_URL": "https://fake-url.supabase.co",
        "SUPABASE_KEY": "fake-key",
        "SUPABASE_DB_URL": "sqlite:///:memory:", 
        "GROQ_API_KEY": "fake-groq-key",
        "SUPABASE_STORAGE_BUCKET": "wardrobe"
    }

# Mock Streamlit session state
if not hasattr(st, "session_state"):
    st.session_state = MagicMock()
    st.session_state.gender_mode = "Men's Fashion"
    st.session_state.wardrobe = []
    st.session_state.messages = []
    st.session_state.user_name = "Test User"
    st.session_state.is_signed_in = True
    st.session_state.planner = {}
    st.session_state.user_season = {}
    st.session_state.audio_cache = {}
    st.session_state.playing_audio_id = None
    st.session_state.show_voice_ui = False
    st.session_state.audio_key = 0
    st.session_state.msg_count = 0
    st.session_state.stop_generating = False
    st.session_state.uploaded_file_temp = None

from modules import database, chat, wardrobe

class TestBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize DB once for all tests"""
        # Create in-memory SQLite engine
        cls.engine = create_engine("sqlite:///:memory:")
        cls.Session = sessionmaker(bind=cls.engine)
        
        # Mock database.get_connection to return an object with a .session property
        # that behaves like st.connection(...).session
        cls.mock_conn = MagicMock()
        
        # Define a context manager for the session
        class SessionContext:
            def __enter__(self):
                self.session = cls.Session()
                return self.session
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.session.close()
        
        cls.mock_conn.session = SessionContext()
        
        # Also mock .query for direct pandas queries
        def mock_query(sql, params=None, ttl=0):
            import pandas as pd
            with cls.engine.connect() as conn:
                return pd.read_sql(sql, conn, params=params)
        cls.mock_conn.query = mock_query

    def setUp(self):
        """Reset session state and DB patch before each test"""
        st.session_state.gender_mode = "Men's Fashion"
        st.session_state.wardrobe = []
        st.session_state.messages = []
        st.session_state.user_name = "Test User"
        st.session_state.is_signed_in = True
        st.session_state.planner = {}
        st.session_state.user_season = {}
        st.session_state.audio_cache = {}
        st.session_state.playing_audio_id = None
        st.session_state.show_voice_ui = False
        st.session_state.audio_key = 0
        st.session_state.msg_count = 0
        st.session_state.stop_generating = False
        st.session_state.uploaded_file_temp = None
        
        # Patch get_connection globally for the test
        self.db_patcher = patch('modules.database.get_connection', return_value=self.mock_conn)
        self.mock_get_conn = self.db_patcher.start()
        
        # Initialize DB tables
        # We need to call init_db but ensure it uses our mocked connection
        # Since we patched get_connection, we need to verify if init_db uses it.
        # modules/database.py:init_db uses st.connection directly, NOT get_connection.
        # So we need to patch st.connection too or refactor init_db.
        # Let's patch st.connection to return our mock_conn
        self.st_conn_patcher = patch('streamlit.connection', return_value=self.mock_conn)
        self.st_conn_patcher.start()
        
        # Now run init_db
        database.init_db()

    def tearDown(self):
        self.db_patcher.stop()
        self.st_conn_patcher.stop()

    # --- 1. Database Connection ---
    def test_database_connection(self):
        """Test if connection is successful and tables exist."""
        try:
            with self.mock_conn.session as s:
                # Check users table
                result = s.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")).fetchone()
                self.assertIsNotNone(result, "Users table should exist")
                
                # Check wardrobe table
                result = s.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='wardrobe'")).fetchone()
                self.assertIsNotNone(result, "Wardrobe table should exist")
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    # --- 2. User Authentication (Mock) ---
    def test_user_authentication(self):
        """Test creating/fetching a 'Test User' (ID: 9999)."""
        user_id = 9999
        username = "Test User"
        
        with self.mock_conn.session as s:
            # Insert Test User
            s.execute(
                text("INSERT INTO users (id, username) VALUES (:id, :username) ON CONFLICT(id) DO NOTHING"),
                {"id": user_id, "username": username}
            )
            s.commit()
            
            # Fetch Test User
            result = s.execute(
                text("SELECT username FROM users WHERE id=:id"),
                {"id": user_id}
            ).fetchone()
            
            self.assertEqual(result[0], username, "Should retrieve the correct username")

    # --- 3. Wardrobe CRUD ---
    @patch("modules.wardrobe.supabase") # Mock Supabase storage calls
    def test_wardrobe_crud(self, mock_supabase):
        """Test Insert, Fetch, Delete for User 9999."""
        user_id = 9999
        category = "Test_Sock"
        image_path = "http://fake.url/sock.jpg"
        
        # A. Insert
        import uuid
        import time
        item_id = str(uuid.uuid4())
        
        with self.mock_conn.session as s:
            s.execute(
                text("INSERT INTO wardrobe (id, user_id, category, gender, image_path, filename, added_at) VALUES (:id, :uid, :cat, :gen, :img, :file, :time)"),
                {"id": item_id, "uid": user_id, "cat": category, "gen": "Men's Fashion", "img": image_path, "file": "sock.jpg", "time": time.time()}
            )
            s.commit()
            
        # B. Fetch
        st.session_state.wardrobe = [] 
        # Ensure get_wardrobe_items uses the mocked connection (it calls get_connection)
        items = wardrobe.get_wardrobe_items(user_id)
        
        # Verify item is in the list
        found = any(item['id'] == item_id for item in items)
        self.assertTrue(found, "Should find the inserted item in wardrobe")
        
        # C. Delete
        # Use the module's delete function
        success = wardrobe.delete_item_from_wardrobe(item_id, "sock.jpg")
        self.assertTrue(success, "Delete function should return True")
        
        # Verify gone from DB
        with self.mock_conn.session as s:
            result = s.execute(text("SELECT * FROM wardrobe WHERE id=:id"), {"id": item_id}).fetchone()
            self.assertIsNone(result, "Item should be deleted from DB")

    # --- 4. Chat Logic ---
    @patch("modules.chat.client")
    def test_chat_logic(self, mock_client):
        """Test AI response generation."""
        # Mock the Groq client response
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Wear a Navy Suit."
        mock_client.chat.completions.create.return_value = mock_completion
        
        messages = [{"role": "user", "content": "I need a suit"}]
        response = chat.get_ai_response(messages)
        
        self.assertIsInstance(response, str, "Response should be a string")
        self.assertNotEqual(response, "", "Response should not be empty")
        self.assertEqual(response, "Wear a Navy Suit.", "Should return the mocked response")

    # --- 5. Mode Switching ---
    def test_mode_switching(self):
        """Verify prompt selection logic."""
        # Test Men's Mode
        prompt_men = chat.get_system_prompt("Men's Fashion", False, "User", [])
        self.assertIn("Gentleman's Style Consultant", prompt_men, "Should contain Men's persona")
        self.assertIn("Navy Jacket with Black Trousers", prompt_men, "Should contain Men's rules")
        
        # Test Women's Mode
        prompt_women = chat.get_system_prompt("Women's Fashion", False, "User", [])
        self.assertIn("Women's Fashion Director", prompt_women, "Should contain Women's persona")
        self.assertIn("Body Shape", prompt_women, "Should contain Women's rules")

if __name__ == "__main__":
    unittest.main()
