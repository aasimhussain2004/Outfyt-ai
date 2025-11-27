import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import json
import sys
import os

# Mock streamlit before importing app
sys.modules["streamlit"] = MagicMock()
import streamlit as st

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Custom Mock for Session State (Dict + Attribute access)
class MockSessionState(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    def __setattr__(self, key, value):
        self[key] = value

# Import functions to test
# Note: Since app.py is a script, importing it might run top-level code.
# We will mock the top-level calls that cause side effects.
with patch("streamlit.set_page_config"), \
     patch("streamlit.markdown"), \
     patch("streamlit.sidebar"), \
     patch("streamlit.session_state", MockSessionState()), \
     patch("streamlit.secrets", {"SUPABASE_DB_URL": "sqlite:///:memory:", "GROQ_API_KEY": "dummy"}), \
     patch("streamlit.connection"), \
     patch("groq.Groq"):
    from app import extract_json_from_text, get_wardrobe_items

def test_json_parsing_valid():
    text = 'Some text {"key": "value"} more text'
    result = extract_json_from_text(text)
    assert result == {"key": "value"}

def test_json_parsing_invalid():
    text = 'No json here'
    result = extract_json_from_text(text)
    assert result is None

def test_json_parsing_nested():
    text = '```json\n{"response_text": "Hello", "lang": "en"}\n```'
    result = extract_json_from_text(text)
    assert result == {"response_text": "Hello", "lang": "en"}

@patch("app.st.connection")
@patch("app.st.session_state")
def test_wardrobe_logic(mock_session_state, mock_connection):
    # Setup Mock DB
    mock_conn = MagicMock()
    mock_connection.return_value = mock_conn
    
    # Mock DataFrame return
    data = {
        "id": ["1", "2"],
        "category": ["Shirt", "Dress"],
        "gender": ["Men's Fashion", "Women's Fashion"],
        "image_path": ["path1", "path2"],
        "filename": ["f1", "f2"],
        "added_at": [1.1, 1.2]
    }
    df = pd.DataFrame(data)
    mock_conn.query.return_value = df
    
    # Setup Session State
    mock_session_state.wardrobe = []
    
    # Call function
    items = get_wardrobe_items(1)
    
    # Verify
    assert len(items) == 2
    assert items[0]["category"] == "Shirt"
    assert items[1]["gender"] == "Women's Fashion"
    
    # Verify Cache Update
    assert len(mock_session_state.wardrobe) == 2

def test_db_connection_mock():
    # Verify we can call the connection logic without crashing
    with patch("app.st.connection") as mock_conn:
        from app import init_db
        init_db()
        mock_conn.assert_called_with("supabase", type="sql", url="sqlite:///:memory:")
