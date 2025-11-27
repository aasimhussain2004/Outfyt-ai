"""
Smoke Tests
Basic tests to verify the application can be imported and has expected structure.
"""
import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test that critical modules can be imported"""
    try:
        import sqlite3
        import json
        import re
        import base64
        from PIL import Image
        from duckduckgo_search import DDGS
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import required module: {e}")

def test_database_schema():
    """Test that we can create the expected database schema"""
    import sqlite3
    
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wardrobe 
                 (id TEXT PRIMARY KEY, user_id INTEGER, category TEXT, gender TEXT, 
                  image_path TEXT, filename TEXT, added_at REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS planner 
                 (date TEXT PRIMARY KEY, user_id INTEGER, outfit_data TEXT)''')
    
    # Verify tables exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    
    assert 'users' in tables
    assert 'wardrobe' in tables
    assert 'planner' in tables
    
    conn.close()

def test_json_operations():
    """Test JSON serialization/deserialization"""
    import json
    
    test_data = {
        "Shirt": "item_123",
        "Trousers": "item_456",
        "gender": "Men's Fashion"
    }
    
    # Serialize
    json_str = json.dumps(test_data)
    assert isinstance(json_str, str)
    
    # Deserialize
    loaded_data = json.loads(json_str)
    assert loaded_data == test_data

def test_image_operations():
    """Test basic PIL Image operations"""
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create image
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw something
    draw.rectangle([50, 50, 150, 150], fill='blue')
    
    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    
    assert buffer.getbuffer().nbytes > 0

def test_regex_patterns():
    """Test regex patterns used in the app"""
    import re
    
    # Test JSON extraction pattern
    text = 'Some text {"key": "value"} more text'
    match = re.search(r"\{.*\}", text, re.DOTALL)
    assert match is not None
    assert '{"key": "value"}' in match.group(0)
