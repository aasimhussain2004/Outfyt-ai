import os
import sys
from streamlit.testing.v1 import AppTest

def test_app_loads():
    """
    Smoke test to verify the Streamlit app loads without error.
    """
    # Get the absolute path to app.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "..", "app.py")
    
    # Initialize the AppTest
    at = AppTest.from_file(app_path)
    
    # Run the app
    at.run()
    
    # Check if there were any exceptions
    assert not at.exception, f"App failed to load with exception: {at.exception}"
    
    # Basic check to ensure title is present (optional, but good practice)
    # Note: This depends on the app actually setting a title or header.
    # at.title matches st.title()
    # at.header matches st.header()
    # We can just check that the script ran to completion.
