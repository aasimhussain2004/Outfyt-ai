import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit secrets before importing modules
import streamlit
if not hasattr(streamlit, 'secrets'):
    streamlit.secrets = {
        "RAZORPAY_KEY_ID": "test",
        "RAZORPAY_KEY_SECRET": "test",
        "TAVILY_API_KEY": "test",
        "SUPABASE_URL": "test",
        "SUPABASE_KEY": "test"
    }

from modules import subscription, search

class TestFreemiumLogic(unittest.TestCase):
    
    @patch('modules.subscription.get_connection')
    def test_check_message_limit_free(self, mock_conn):
        # Mock DB result
        mock_session = MagicMock()
        mock_conn.return_value.session = mock_session
        # Result: is_premium=False, count=10, last_active=today
        mock_session.__enter__.return_value.execute.return_value.fetchone.return_value = [False, 10, datetime.date.today(), 0, None]
        
        can_send = subscription.check_message_limit(1)
        self.assertTrue(can_send)

    @patch('modules.subscription.get_connection')
    def test_check_message_limit_exceeded(self, mock_conn):
        mock_session = MagicMock()
        mock_conn.return_value.session = mock_session
        # Result: is_premium=False, count=20
        mock_session.__enter__.return_value.execute.return_value.fetchone.return_value = [False, 20, datetime.date.today(), 0, None]
        
        can_send = subscription.check_message_limit(1)
        self.assertFalse(can_send)

    @patch('modules.subscription.get_connection')
    def test_check_wardrobe_limit_free(self, mock_conn):
        mock_session = MagicMock()
        mock_conn.return_value.session = mock_session
        mock_session.__enter__.return_value.execute.return_value.fetchone.return_value = [False, 0, datetime.date.today(), 0, None]
        
        # Mock actual count
        mock_conn.return_value.query.return_value.iloc.__getitem__.return_value = 4
        
        can_add = subscription.check_wardrobe_limit(1)
        self.assertTrue(can_add)

    @patch('modules.search.tavily_client')
    def test_search_tavily(self, mock_client):
        # Mock the client instance directly
        mock_client.search.return_value = {
            "results": [
                {"title": "Test Item", "url": "http://test.com", "content": "Desc"}
            ],
            "images": ["http://test.com/img.jpg"]
        }
        
        results = search.search_tavily("blue shirt")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Item")

if __name__ == '__main__':
    unittest.main()
