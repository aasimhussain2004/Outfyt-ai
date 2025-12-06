import streamlit as st
import uuid
import time
from sqlalchemy import text
from modules import database, auth, chat, wardrobe, planner, color, onboarding, subscription, tryon

# Page Config
st.set_page_config(page_title="Outfyt AI", page_icon="assets/logo.png", layout="wide")

# --- MASTER THEME BLOCK (Static) ---
st.markdown("""
<style>
    /* 1. Global Reset & Background */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed !important;
        color: #E0E0E0;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* 2. Text Visibility (Global) */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stCaption, li, div {
        color: #ffffff !important;
    }

    /* 3. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 4. Sidebar Toggle Button (Expanded & Collapsed) */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="stSidebarCollapsedControl"] {
        color: #C5B358 !important;
        background-color: #1a1a2e !important;
        border: 2px solid #C5B358 !important;
        border-radius: 8px !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        width: 2.5rem !important;
        height: 2.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 0 10px rgba(197, 179, 88, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Icon Color */
    [data-testid="stSidebarCollapseButton"] svg, 
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] i, 
    [data-testid="stSidebarCollapsedControl"] i {
        fill: #C5B358 !important;
        color: #C5B358 !important;
        stroke: #C5B358 !important;
    }
    
    /* Hover State */
    [data-testid="stSidebarCollapseButton"]:hover, 
    [data-testid="stSidebarCollapsedControl"]:hover {
        background-color: #C5B358 !important;
        box-shadow: 0 0 15px rgba(197, 179, 88, 0.6) !important;
        transform: scale(1.05) !important;
    }
    
    /* Icon Hover Color */
    [data-testid="stSidebarCollapseButton"]:hover svg, 
    [data-testid="stSidebarCollapsedControl"]:hover svg,
    [data-testid="stSidebarCollapseButton"]:hover i, 
    [data-testid="stSidebarCollapsedControl"]:hover i {
        fill: #1a1a2e !important;
        color: #1a1a2e !important;
        stroke: #1a1a2e !important;
    }

    /* 5. Buttons (Gold Theme) */
    div.stButton > button:not([kind="primary"]), div.stFormSubmitButton > button:not([kind="primary"]) {
        background-color: #1a1a2e !important; 
        color: #C5B358 !important; 
        border: 2px solid #C5B358 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    div.stButton > button:not([kind="primary"]):hover {
        background-color: #C5B358 !important;
        color: #1a1a2e !important;
    }
    /* Primary Button (Red) */
    button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }

    /* 6. Inputs & Selectboxes */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div, div[data-baseweb="base-input"] {
        background-color: #262730 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border-color: #444 !important;
    }
    
    /* 7. Dropdowns & Menus */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #262730 !important;
    }
    li[role="option"] {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    li[role="option"]:hover {
        background-color: #C5A059 !important;
    }

    /* 8. Dialogs & Modals (The Nuclear Fix) */
    div[data-testid="stDialog"], div[role="dialog"] {
        background-color: #1a1a2e !important;
        color: white !important;
    }
    div[data-testid="stDialog"] > div, div[role="dialog"] > div {
        background-color: #1a1a2e !important;
        color: white !important;
        border: 2px solid #C5B358 !important;
        border-radius: 15px !important;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] p, div[data-testid="stDialog"] label {
        color: #ffffff !important;
    }
    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #ffffff !important;
        background-color: transparent !important;
    }
    
    /* 9. File Uploader */
    [data-testid="stFileUploader"] button {
        color: #1a1a2e !important;
        background-color: #ffffff !important;
    }

    /* 10. Expander */
    [data-testid="stExpander"] details > summary {
        color: #ffffff !important;
        background-color: #2a2a4e !important;
        border: 1px solid #C5B358 !important;
    }

    /* 11. Chat Input Fix (Super Nuclear) */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
    }
    
    /* Target the internal wrapper provided by BaseWeb - Force BLACK */
    [data-testid="stChatInput"] div[data-baseweb="base-input"] {
        background-color: #000000 !important; /* Pure Black */
        border: 2px solid #C5B358 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    }

    /* The actual textarea - Force BLACK background, WHITE text */
    [data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #ffffff !important;
        caret-color: #C5B358 !important;
    }

    /* Placeholder Text */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #aaaaaa !important;
    }

    /* Send Button */
    [data-testid="stChatInput"] button {
        color: #C5B358 !important;
        background-color: transparent !important;
        border: none !important;
    }
    [data-testid="stChatInput"] button:hover {
        color: #ffffff !important;
        background-color: rgba(197, 179, 88, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB
# database.init_db() # Removed for Supabase migration

# Initialize Session & Auth (Returns dummy user_id=1)
# Initialize Session & Auth (Returns dummy user_id=1)
# Initialize Session & Auth (Returns dummy user_id=1)
user_id = auth.init_user_session()

# Fix UUID: Ensure user_id is a valid UUID if it's "1" (legacy)
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
user_id = st.session_state.user_id

# --- SYNC PREMIUM STATUS ---
# Always fetch latest status from DB to ensure persistence across reloads
try:
    user_status = subscription.get_user_status(user_id)
    if user_status:
        st.session_state.is_premium = user_status.get("is_premium", False)
except Exception:
    pass # Fail gracefully, default to False (Free)

if "show_upgrade_dialog" not in st.session_state:
    st.session_state.show_upgrade_dialog = False

if "tutorial_completed" not in st.session_state:
    st.session_state.tutorial_completed = False

@st.dialog("🌟 Upgrade to Outfyt Premium")
def show_upgrade():
    # 0. Enforce Sign In First
    if not st.session_state.get("is_signed_in", False):
        st.warning("Please Sign In first to upgrade.")
        st.write("Your premium status needs to be linked to your account.")
        if st.button("Sign In Now", type="primary"):
            st.session_state.temp_signin = True
            st.rerun()
        return

    # Check if user is ALREADY premium (Success State)
    # Check if user is ALREADY premium (Success State)
    if st.session_state.get("is_premium", False):
        # Only show balloons if this was a fresh upgrade (triggered by payment)
        if st.session_state.get("just_upgraded", False):
            st.balloons()
            st.success("🎉 You are a Pro User!")
            st.session_state.just_upgraded = False # Reset
        else:
            st.info("✅ You are already a Pro User")
            
        st.markdown("Enjoy unlimited access to all features.")
        if st.button("Close"):
            st.rerun()
        return

    st.write("Unlock the full potential of your personal AI stylist.")
    
    st.write("Unlock the full potential of your personal AI stylist.")
    
    # 1. Generate Links Safely
    with st.spinner("Loading plans..."):
        link_day = subscription.create_payment_link(st.session_state.user_id, amount=2900, description="1 Day Pass")
        link_month = subscription.create_payment_link(st.session_state.user_id, amount=19900, description="Monthly Premium")
        link_year = subscription.create_payment_link(st.session_state.user_id, amount=99900, description="Annual Premium")

    # 2. Display 3-Column Pricing
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("### ⚡ 1 Day")
            st.markdown("## ₹29")
            st.caption("Quick Style Check")
            st.write("• Unlimited Chat (24h)")
            st.write("• Full Wardrobe Access")
            st.divider()
            if link_day:
                st.link_button("Get Day Pass", link_day.get("short_url"), use_container_width=True)

    with col2:
        with st.container(border=True):
            st.markdown("### 🌟 Monthly")
            st.markdown("## ₹199")
            st.caption("Most Popular")
            st.write("• Unlimited Everything")
            st.write("• Priority Support")
            st.divider()
            if link_month:
                st.link_button("Get Monthly", link_month.get("short_url"), type="primary", use_container_width=True)

    with col3:
        with st.container(border=True):
            st.markdown("### 💎 Annual")
            st.markdown("## ₹999")
            st.caption("Best Value")
            st.write("• Save 60%")
            st.write("• All Future Features")
            st.divider()
            if link_year:
                st.link_button("Get Annual", link_year.get("short_url"), use_container_width=True)

# --- Payment Listener (Post-Redirect) ---
if "razorpay_payment_link_status" in st.query_params:
    status = st.query_params["razorpay_payment_link_status"]
    
    # Recover User ID from Query Params if lost
    if "user_id" in st.query_params:
        st.session_state.user_id = st.query_params["user_id"]
        user_id = st.session_state.user_id

    if status == "paid":
        # 1. Update Database (Critical)
        try:
            subscription.verify_and_upgrade_user(database.supabase, user_id)

            # 2. Update Local Session
            st.session_state.is_premium = True
            st.session_state.tutorial_completed = True
            st.session_state.trigger_upgrade = True # Trigger the dialog (Success Mode)
            st.session_state.just_upgraded = True # Flag for balloons
            
            # Force reload of user status
            st.session_state.user_status = subscription.get_user_status(user_id)

            # 3. Clear URL to prevent loop (Keep user_id)
            st.query_params.clear()
            st.query_params["user_id"] = user_id
            st.rerun()
        except Exception as e:
            st.error(f"Payment verification failed: {e}")

# --- Onboarding Check ---
# Sync session state with DB if needed, but prioritize session state
if not st.session_state.tutorial_completed:
    try:
        if database.supabase:
            result = database.supabase.table("user_profiles").select("tutorial_completed").eq("user_id", str(user_id)).execute()
            if result.data and result.data[0].get("tutorial_completed"):
                st.session_state.tutorial_completed = True
    except Exception:
        pass 

if not st.session_state.tutorial_completed:
    onboarding.show_tutorial(user_id)
else:
    # Only check for upgrades if tutorial is done
    pass

# Sidebar Help Button (Forces Tutorial)
with st.sidebar:
    if st.button("❓ Help", use_container_width=True):
        onboarding.show_tutorial(user_id)
    
    # Upgrade Button (Below Help)
    is_premium = st.session_state.get("is_premium", False)
    if not is_premium:
        if st.button("🚀 Upgrade to Premium", use_container_width=True):
            show_upgrade()
    else:
        st.success("👑 You are a Pro User")
        
    st.divider()
    # Subscription Status (Visuals)
    status = subscription.get_user_status(user_id)
    if status:
        if not status["is_premium"]:
            st.markdown("### 🆓 Free Tier")
            st.progress(min(status["daily_msg_count"] / 20, 1.0), text=f"Messages: {status['daily_msg_count']}/20")

# --- Dynamic Branding (Theme Shifting) ---
if st.session_state.gender_mode == "Men's Fashion":
    accent_color = "#C5A059" # Gold
    accent_hover = "#B08D45"
    text_highlight = "#000000"
else:
    accent_color = "#E0BFB8" # Soft Rose Gold
    accent_hover = "#D4AF37" # Gold/Rose mix
    text_highlight = "#333333"

# --- CSS Injection (Dynamic) ---
st.markdown(f"""
<style>
    /* Global Reset & Background */
    html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed !important;
        color: #E0E0E0;
        font-family: 'Helvetica Neue', sans-serif;
    }}
    
    /* Main App Container */
    .stApp {{
        background: transparent !important;
    }}

    /* Header (Transparent) */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* Text Colors */
    .stMarkdown, .stText, p, h1, h2, h3, label, div {{
        color: #E0E0E0 !important;
    }}
    
    /* Glass Buttons (General) */
    .stButton button {{
        background: linear-gradient(135deg, {accent_color} 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #764ba2 0%, {accent_color} 100%);
    }}

    /* Sidebar Link-Style Buttons */
    [data-testid="stSidebar"] .stButton button {{
        background: transparent !important;
        box-shadow: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding-left: 0 !important;
        color: #B0B0B0 !important;
        font-weight: 400 !important;
    }}
    [data-testid="stSidebar"] .stButton button:hover {{
        color: #FFFFFF !important;
        background: rgba(255,255,255,0.05) !important;
        transform: none !important;
    }}
    /* Primary "New Chat" Button in Sidebar - Override Link Style */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {accent_color} 0%, #764ba2 100%) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        justify-content: center !important;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    
    /* User Message Specific Style */
    [data-testid="stChatMessage"]:nth-child(odd) {{
        background-color: rgba(118, 75, 162, 0.15);
        border: 1px solid rgba(118, 75, 162, 0.3);
    }}

    /* Dividers */
    hr {{
        border-color: rgba(255, 255, 255, 0.2);
    }}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {{
        width: 8px;
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(118, 75, 162, 0.5);
        border-radius: 10px;
    }}

    /* --- On-Demand Audio Button Styling (Dynamic) --- */
    .stChatMessage .stButton button {{
        background: transparent !important;
        border: 2px solid {accent_color} !important;
        color: {accent_color} !important;
        border-radius: 20px !important;
        padding: 0.3rem 1rem !important;
        font-size: 0.9rem !important;
        box-shadow: 0 0 10px rgba(197, 160, 89, 0.1) !important;
        transition: all 0.3s ease !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    .stChatMessage .stButton button:hover {{
        background: rgba(197, 160, 89, 0.1) !important;
        box-shadow: 0 0 20px rgba(197, 160, 89, 0.4) !important;
        transform: scale(1.05) !important;
        color: #FFF !important;
    }}

    /* --- Waveform Animation CSS --- */
    .waveform {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        height: 30px;
        gap: 4px;
        margin-top: 10px;
    }}
    
    .bar {{
        width: 4px;
        background-color: {accent_color};
        border-radius: 2px;
        animation: wave 1s ease-in-out infinite;
    }}
    
    .bar:nth-child(1) {{ animation-delay: 0.0s; height: 10px; }}
    .bar:nth-child(2) {{ animation-delay: 0.1s; height: 15px; }}
    .bar:nth-child(3) {{ animation-delay: 0.2s; height: 20px; }}
    .bar:nth-child(4) {{ animation-delay: 0.3s; height: 15px; }}
    .bar:nth-child(5) {{ animation-delay: 0.4s; height: 10px; }}
    
    @keyframes wave {{
        0%, 100% {{ transform: scaleY(1); }}
        50% {{ transform: scaleY(2); }}
    }}
    
    /* --- Color Swatch Styling --- */
    .color-swatch-container {{
        display: flex;
        gap: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }}
    .color-swatch {{
        width: 50px;
        height: 50px;
        border-radius: 50%;
        border: 2px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }}
    .color-swatch:hover {{
        transform: scale(1.2);
        border-color: #FFF;
    }}
    .season-title {{
        font-size: 2em;
        font-weight: bold;
        background: linear-gradient(to right, {accent_color}, #FDB931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }}
    
    /* --- 1. GLOBAL INPUTS (Text, Date, Select) --- */
    /* Force the container of all inputs to be Dark Grey */
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] {{
        background-color: #262730 !important;
        color: #FAFAFA !important;
        border-color: #444 !important;
    }}
    /* Force text inside inputs to be White */
    input {{
        color: #FAFAFA !important;
    }}

    /* --- 2. DROPDOWNS & POPOVERS (The Menu Lists) --- */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-testid="stSelectboxVirtualDropdown"] {{
        background-color: #262730 !important;
    }}
    /* The individual options */
    li[role="option"] {{
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }}
    li[role="option"] div {{
        color: #FAFAFA !important;
    }}
    /* Hover State (Gold) */
    li[role="option"]:hover {{
        background-color: #C5A059 !important;
    }}
    li[role="option"]:hover div {{
        color: #000000 !important;
    }}

    /* --- 3. DATE PICKER (For the Planner) --- */
    div[data-baseweb="calendar"] {{
        background-color: #262730 !important;
    }}
    div[data-baseweb="calendar"] button {{
        color: #FAFAFA !important;
    }}

    /* --- 4. TOASTS (Notifications) --- */
    div[data-testid="stToast"] {{
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }}

    /* --- Wardrobe Gallery Styling --- */
    .wardrobe-item {{
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 10px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .wardrobe-item img {{
        border-radius: 10px;
        max-width: 100%;
        height: auto;
        object-fit: cover;
    }}
    .wardrobe-caption {{
        margin-top: 10px;
        font-weight: 600;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.8); /* Strong shadow for contrast */
        color: #FFFFFF !important;
        font-size: 1.1rem;
    }}
    /* Custom White Chat Input */
    .stChatInput textarea {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important;
        border: 2px solid #C5B358 !important;
    }}
    .stChatInput textarea::placeholder {{
        color: #666666 !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- Dynamic Header ---
mode = st.session_state.get('gender_mode', "Men's Fashion")

col_h1, col_h2 = st.columns([1.5, 10])
with col_h1:
    st.image("assets/logo.png", width=120)

with col_h2:
    if mode == "Men's Fashion":
        st.markdown("# Outfyt AI | Gentleman's Companion")
        st.caption("High-End Men's Fashion Consultant")
    else:
        st.markdown("# Outfyt AI | Women's Style Director")
        st.caption("High-End Women's Fashion Consultant")

# Main UI
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "🎨 Color Analysis", "🧥 Wardrobe", "📅 Planner", "✨ Virtual Try-On"])

with tab1:
    chat.handle_chat()

with tab2:
    color.display_color_analysis()

with tab3:
    wardrobe.display_wardrobe()

with tab4:
    planner.display_outfit_planner()

with tab5:
    tryon.show_tryon_page()

# Trigger Upgrade Dialog from Modules
if st.session_state.get("trigger_upgrade", False):
    # 1. If not signed in, force sign-in flow FIRST
    if not st.session_state.get("is_signed_in", False):
        st.session_state.temp_signin = True
        # Do NOT reset trigger_upgrade yet; wait for sign-in to complete
        
    # 2. If signed in (and not currently signing in), show upgrade
    elif not st.session_state.get("temp_signin", False):
        st.session_state.trigger_upgrade = False # Reset flag
        show_upgrade()

if __name__ == "__main__":
    pass
