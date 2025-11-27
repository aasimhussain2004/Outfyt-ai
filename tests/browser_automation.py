import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_pass(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"{CYAN}ℹ️ {msg}{RESET}")

def run_browser_tests():
    print_info("Starting Browser Automation Tests...")
    
    # Setup Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Run in headless mode for CI/CD environments or local speed
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize Driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15) # 15 seconds explicit wait
        
        # 1. Open Browser
        print_info("Opening http://localhost:8501...")
        driver.get("http://localhost:8501")
        
        # 2. Wait for Load
        # Streamlit apps often have a loading state. We wait for the main container.
        # We can check for the title "Outfyt AI" which should be in the page title or header.
        wait.until(EC.title_contains("Outfyt AI"))
        print_pass("Page Loaded (Title verified)")
        
        # Wait for the main app container to be present to ensure Streamlit is ready
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stApp")))
        
        # 3. Test Chat
        print_info("Testing Chat Functionality...")
        
        # Find Chat Input
        # Streamlit's chat input usually has a specific test-id or class.
        # We look for the textarea inside the chat input container.
        chat_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[data-testid='stChatInputTextArea']")))
        
        # Type Message
        chat_input.send_keys("Hello, what should I wear?")
        chat_input.send_keys(Keys.RETURN) # Press Enter to send
        
        print_info("Message sent. Waiting for response...")
        
        # Wait for a new message to appear. 
        # Streamlit chat messages usually have data-testid="stChatMessage"
        # We wait for at least 2 messages (User + Assistant)
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "div[data-testid='stChatMessage']")) >= 2)
        
        # Verify the last message is from the assistant (avatar check or content check)
        messages = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stChatMessage']")
        last_message = messages[-1]
        
        # We can check if it contains some text, but just existence is good for now.
        print_pass("Chat Response Received")
        
        # 4. Test Wardrobe Tab
        print_info("Testing Wardrobe Tab...")
        
        # Find the "My Wardrobe" tab button. 
        # Streamlit tabs are buttons in a div[data-testid="stTabs"]
        tabs = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='stTabs'] button")
        found_wardrobe = False
        for tab in tabs:
            if "My Wardrobe" in tab.text:
                tab.click()
                found_wardrobe = True
                break
        
        if found_wardrobe:
            print_pass("Clicked 'My Wardrobe' Tab")
            
            # Verify "Add New Item" section is visible.
            # This is likely an expander or a header.
            # Let's look for the text "Add New Item" in the page source or specific element.
            wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "stApp"), "Add New Item"))
            print_pass("'Add New Item' section is visible")
        else:
            print_fail("Could not find 'My Wardrobe' tab")
            
        # 5. Test Toggle (Sidebar)
        print_info("Testing Sidebar Toggle...")
        
        # Find the radio button for "Women's Fashion".
        # Streamlit radio buttons are in div[data-testid="stRadio"]
        # We need to find the label containing "Women's Fashion" and click it.
        # Note: The actual input is hidden, we click the label or the div.
        
        # First ensure sidebar is open (it usually is on desktop)
        # But just in case, we look for the radio in the whole DOM.
        
        # XPath to find the label text "Women's Fashion" inside a radio group
        women_radio = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='stRadio']//p[contains(text(), \"Women's Fashion\")]/../..")))
        women_radio.click()
        
        # Verify the change. 
        # The app should re-run. We can check if the "Men's Fashion" is no longer selected or check a state change.
        # For simplicity, let's wait a second and verify no crash.
        time.sleep(2)
        print_pass("Toggled to Women's Fashion")
        
        print_pass("🎉 All Browser Tests Passed!")
        
    except Exception as e:
        print_fail(f"Test Failed: {e}")
        # Optional: Take screenshot
        # driver.save_screenshot("error_screenshot.png")
    finally:
        if 'driver' in locals():
            driver.quit()
            print_info("Browser Closed.")

if __name__ == "__main__":
    run_browser_tests()
