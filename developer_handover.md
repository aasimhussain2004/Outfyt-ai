# Developer Handover Document

## 1. Project Overview
**Outfyt AI** is a Streamlit-based fashion assistant application featuring Virtual Try-On, AI Chat, Wardrobe Management, Outfit Planning, and Personal Color Analysis.

## 2. File Structure
```text
.
├── .github/
│   └── workflows/
│       └── main.yml
├── .streamlit/
│   └── secrets.toml
├── modules/
│   ├── auth.py
│   ├── chat.py
│   ├── color.py
│   ├── database.py
│   ├── onboarding.py
│   ├── planner.py
│   ├── search.py
│   ├── subscription.py
│   ├── tryon.py
│   └── wardrobe.py
├── static/
│   └── audio/
├── temp/
├── tests/
├── app.py
├── requirements.txt
└── README.md
```

## 3. Environment Variables
Required keys for `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "HIDDEN"
SUPABASE_URL = "HIDDEN"
SUPABASE_KEY = "HIDDEN"
SUPABASE_DB_URL = "HIDDEN" # postgresql://...
SUPABASE_STORAGE_BUCKET = "wardrobe-images"
RAZORPAY_KEY_ID = "HIDDEN"
RAZORPAY_KEY_SECRET = "HIDDEN"
TAVILY_API_KEY = "HIDDEN"
HUGGINGFACE_TOKEN = "HIDDEN" # Optional, for VTON
```

## 4. Database Schema (Supabase)

### `user_profiles`
- `user_id` (TEXT, PK): UUID
- `name` (TEXT)
- `is_premium` (BOOLEAN)
- `tutorial_completed` (BOOLEAN)

### `user_usage`
- `user_id` (TEXT, PK)
- `is_premium` (BOOLEAN)
- `daily_msg_count` (INTEGER)
- `last_active_date` (TEXT/DATE)
- `wardrobe_count` (INTEGER)
- `subscription_end_date` (TEXT)

### `wardrobe`
- `id` (TEXT, PK): UUID
- `user_id` (TEXT)
- `category` (TEXT)
- `gender` (TEXT): "Men's Fashion" or "Women's Fashion"
- `image_path` (TEXT): Public URL
- `filename` (TEXT)
- `added_at` (FLOAT)

### `planner`
- `date` (TEXT, PK): YYYY-MM-DD
- `user_id` (TEXT)
- `outfit_data` (TEXT): JSON String

### `chat_history`
- `id` (INTEGER, PK)
- `user_id` (TEXT)
- `role` (TEXT)
- `content` (TEXT)
- `timestamp` (DATETIME)

---

# 5. Codebase


## requirements.txt
`	ext
streamlit
groq
supabase
pandas
plotly
gtts
sqlalchemy
psycopg2-binary
Pillow
selenium
webdriver-manager
pytest
duckduckgo-search
razorpay
tavily-python
ruff
gradio_client
## requirements.txt
`	ext
streamlit
groq
supabase
pandas
plotly
gtts
sqlalchemy
psycopg2-binary
Pillow
selenium
webdriver-manager
pytest
duckduckgo-search
razorpay
tavily-python
ruff
gradio_client
`"; Add-Content developer_handover.md 
## modules/auth.py
`python
import streamlit as st
import uuid

from modules import database

def init_user_session():
    """Initialize session state and render sidebar auth/mode UI."""
    
    # 0. Check for Persistent Login (Query Params)
    if "user_id" in st.query_params:
        qp_user_id = st.query_params["user_id"]
        # Validate UUID format roughly
        if len(qp_user_id) > 20: 
            st.session_state.user_id = qp_user_id
            st.session_state.is_signed_in = True
            
            # Fetch User Name if not set
            if "user_name" not in st.session_state:
                try:
                    response = database.supabase.table("user_profiles").select("name").eq("user_id", st.session_state.user_id).execute()
                    if response.data:
                        st.session_state.user_name = response.data[0].get("name", "User")
                except:
                    st.session_state.user_name = "User"

    # Session State Initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "stop_generating" not in st.session_state:
        st.session_state.stop_generating = False
    if "msg_count" not in st.session_state:
        st.session_state.msg_count = 0
    if "guest_msg_count" not in st.session_state:
        st.session_state.guest_msg_count = 0
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "is_signed_in" not in st.session_state:
        st.session_state.is_signed_in = False
    if "last_audio_input" not in st.session_state:
        st.session_state.last_audio_input = None
    if "audio_key" not in st.session_state:
        st.session_state.audio_key = 0
    if "audio_cache" not in st.session_state:
        st.session_state.audio_cache = {}
    if "playing_audio_id" not in st.session_state:
        st.session_state.playing_audio_id = None
    if "user_season" not in st.session_state:
        st.session_state.user_season = None
    if "wardrobe" not in st.session_state:
        st.session_state.wardrobe = []
    if "planner" not in st.session_state:
        st.session_state.planner = {}
    if "show_voice_ui" not in st.session_state:
        st.session_state.show_voice_ui = False
    if "show_upload_dialog" not in st.session_state:
        st.session_state.show_upload_dialog = False
    if "gender_mode" not in st.session_state:
        st.session_state.gender_mode = "Men's Fashion"
    if "prev_mode" not in st.session_state:
        st.session_state.prev_mode = st.session_state.gender_mode
    if "shopping_results" not in st.session_state:
        st.session_state.shopping_results = {}
    if "language" not in st.session_state:
        st.session_state.language = "English (US)"

    # Sidebar
    with st.sidebar:
        col_logo, col_title = st.columns([2, 3])
        with col_logo:
            st.image("assets/logo.png", width=180)
        with col_title:
            st.markdown("<h3 style='margin-top: 20px; margin-bottom: 10; font-size: 22px;'>Style Companion</h3>", unsafe_allow_html=True)
        
        # 1. The Switch (Sidebar Toggle)
        mode = st.radio(
            "Mode", 
            ["Men's Fashion", "Women's Fashion"], 
            horizontal=True, 
            key="gender_mode_radio"
        )
        st.session_state.gender_mode = mode
        
        # Mode Switch Notification
        if st.session_state.gender_mode != st.session_state.prev_mode:
            if st.session_state.gender_mode == "Women's Fashion":
                st.toast("Activating Women's Style Mode... 💃", icon='✨')
            else:
                st.toast("Activating Gentleman's Mode... 👔", icon='🎩')
            st.session_state.prev_mode = st.session_state.gender_mode

        if st.button("✨ New Chat", use_container_width=True, type="primary"):
            if st.session_state.messages:
                st.session_state.chat_history.append(st.session_state.messages)
            st.session_state.messages = []
            st.session_state.msg_count = 0 
            st.session_state.audio_cache = {}
            st.session_state.playing_audio_id = None
            st.session_state.shopping_results = {}
            st.rerun()
            
        st.subheader("History")
        if not st.session_state.chat_history:
            st.caption("No recent chats.")
        else:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                # Use the first user message as the title
                title = "New Chat"
                for msg in chat:
                    if msg["role"] == "user":
                        title = msg["content"][:20] + "..."
                        break
                if st.button(title, key=f"hist_{i}", use_container_width=True):
                    st.session_state.messages = chat
                    st.rerun()
        
        st.divider()
        
        if st.session_state.is_signed_in:
            st.write(f"**{st.session_state.user_name}**")
            if st.button("Sign Out", use_container_width=True):
                st.session_state.is_signed_in = False
                st.session_state.user_name = None
                st.session_state.user_season = None 
                # Clear Query Params
                st.query_params.clear()
                # Generate new temp ID
                st.session_state.user_id = str(uuid.uuid4())
                st.rerun()
        else:
            if st.button("Sign In", use_container_width=True):
                st.session_state.temp_signin = True
                st.rerun()

    # Handle Dialogs
    if st.session_state.get("temp_signin"):
        sign_in_dialog_func()

    # Persistent User ID for Session (Fallback)
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
        
    return st.session_state.user_id

@st.dialog("Sign In")
def sign_in_dialog_func():
    st.write("Enter your Name to complete Sign In:")
    st.caption("This will save your data permanently.")
    name = st.text_input("Name")
    if name:
        if st.button("Confirm"):
            # 1. Check if user exists in DB
            try:
                response = database.supabase.table("user_profiles").select("*").eq("name", name).execute()
                
                if response.data:
                    # User Exists - Load Data
                    user_data = response.data[0]
                    st.session_state.user_id = user_data['user_id']
                    st.session_state.user_name = user_data['name']
                    st.toast(f"Welcome back, {name}!", icon="👋")
                else:
                    # New User - Create in DB
                    new_id = str(uuid.uuid4())
                    database.supabase.table("user_profiles").insert({
                        "user_id": new_id,
                        "name": name,
                        "is_premium": False
                    }).execute()
                    st.session_state.user_id = new_id
                    st.session_state.user_name = name
                    st.toast(f"Account created for {name}!", icon="🎉")
                
                # 2. Update Session & Query Params
                st.session_state.is_signed_in = True
                st.session_state.temp_signin = False
                st.query_params["user_id"] = st.session_state.user_id
                st.rerun()
                
            except Exception as e:
                st.error(f"Sign in failed: {e}")

@st.dialog("Sign In Required")
def sign_in_required_dialog():
    st.write("You've reached the free limit of 5 messages.")
    st.write("Sign in to continue chatting with Outfyt AI.")
    if st.button("Continue with Google", use_container_width=True):
        st.session_state.temp_signin = True
        st.rerun()
`"; Add-Content developer_handover.md 
## modules/wardrobe.py
`python
import streamlit as st
import pandas as pd
import time
import uuid
import io
from PIL import Image
from sqlalchemy import text
from modules.database import get_connection, supabase

def display_wardrobe():
    st.header("🧥 My Digital Wardrobe")
    st.write(f"Catalog your **{st.session_state.gender_mode}** items.")
    
    # --- STEP 1: UPLOAD SECTION (Reactive) ---
    MENS_CATEGORIES = ['Suit', 'Blazer', 'Shirt', 'T-Shirt', 'Trousers', 'Jeans', 'Shoes', 'Accessory']
    WOMENS_CATEGORIES = ['Dress', 'Saree', 'Lehenga', 'Top', 'Skirt', 'Jeans', 'Trousers', 'Heels', 'Accessory']
    current_categories = MENS_CATEGORIES if st.session_state.gender_mode == "Men's Fashion" else WOMENS_CATEGORIES

    with st.container():
        from modules import subscription
        user_id = st.session_state.get("user_id", 1)

        # --- 0. GUEST CHECK ---
        if not st.session_state.get("is_signed_in", False):
            st.info("🔒 Sign In to build your digital wardrobe.")
            if st.button("Sign In to Upload", key="wardrobe_signin_btn"):
                st.session_state.temp_signin = True
                st.rerun()
            st.divider()
            # Fall through to show grid (read-only) or empty state
        
        # --- FREEMIUM CHECK ---
        elif not subscription.check_wardrobe_limit(supabase, user_id):
            # Get actual count for display
            try:
                # Fetch all items to analyze distribution
                all_items = supabase.table('wardrobe').select("gender, category").eq('user_id', str(user_id)).execute().data
                total_count = len(all_items)
                
                # Analyze distribution
                mens_count = sum(1 for i in all_items if i.get('gender') == "Men's Fashion")
                womens_count = sum(1 for i in all_items if i.get('gender') == "Women's Fashion")
                
                breakdown_msg = f"**Breakdown:** {mens_count} Men's, {womens_count} Women's."
            except Exception as e:
                # If error is not "Limit Reached" but a DB error, we should probably show it or handle it.
                # But for now, let's assume it's the limit fallback.
                # DEBUG: Show error to user to confirm hypothesis
                st.error(f"Database Error: {e}")
                total_count = 5
                breakdown_msg = ""
                mens_count = 0
                womens_count = 0
            
            st.error(f"🚫 Total Wardrobe Limit Reached ({total_count}/5 items).")
            if breakdown_msg:
                st.caption(breakdown_msg)
                
            if st.session_state.gender_mode == "Men's Fashion" and mens_count == 0 and womens_count > 0:
                st.info(f"💡 You have {womens_count} items in **Women's Fashion**. Switch modes to view or delete them.")
            elif st.session_state.gender_mode == "Women's Fashion" and womens_count == 0 and mens_count > 0:
                st.info(f"💡 You have {mens_count} items in **Men's Fashion**. Switch modes to view or delete them.")

            st.markdown("---")
            st.write("### 🔓 Unlock Unlimited Wardrobe")
            if st.button("🚀 Upgrade to Premium", key="wardrobe_upgrade_btn", type="primary"):
                st.session_state.trigger_upgrade = True
                st.rerun()
                
            with st.expander("🔍 Debug Info"):
                st.write(f"User ID: `{user_id}`")
                st.write(f"Premium Status: `{subscription.get_user_status(user_id).get('is_premium')}`")
                st.write(f"Current Mode: `{st.session_state.gender_mode}`")
        else:
            c_up, c_cat, c_btn = st.columns([2, 2, 1])
            with c_up:
                wardrobe_file = st.file_uploader("Upload Cloth Image", type=["jpg", "jpeg", "png"], key="wardrobe_uploader_reactive")
            with c_cat:
                category = st.selectbox("Category", current_categories, key="wardrobe_cat_reactive")
            with c_btn:
                st.write("") # Spacer
                st.write("")
                if st.button("Add to Closet", type="primary", use_container_width=True):
                    if wardrobe_file:
                        # Inline Upload Logic for Max Reactivity
                        try:
                            # 1. Compress
                            image = Image.open(wardrobe_file)
                            if image.mode in ("RGBA", "P"): image = image.convert("RGB")
                            
                            max_width = 1000
                            if image.width > max_width:
                                ratio = max_width / float(image.width)
                                new_height = int(float(image.height) * ratio)
                                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                                
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format='JPEG', quality=80)
                            img_byte_arr.seek(0)
                            
                            # 2. Upload
                            bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
                            file_ext = "jpg"
                            unique_filename = f"{uuid.uuid4()}.{file_ext}"
                            
                            if supabase:
                                supabase.storage.from_(bucket_name).upload(
                                    unique_filename,
                                    img_byte_arr.getvalue(),
                                    {"content-type": "image/jpeg"}
                                )
                                
                                public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
                                
                                # 3. DB Insert
                                conn = get_connection()
                                with conn.session as s:
                                    s.execute(
                                        text("INSERT INTO wardrobe (id, user_id, category, gender, image_path, filename, added_at) VALUES (:id, :user_id, :category, :gender, :image_path, :filename, :added_at)"),
                                        {"id": str(uuid.uuid4()), "user_id": user_id, "category": category, "gender": st.session_state.gender_mode, "image_path": public_url, "filename": unique_filename, "added_at": time.time()}
                                    )
                                    s.commit()
                                
                                st.success("Added!")
                                time.sleep(1) # Visual feedback
                                st.rerun() # FORCE RELOAD
                            else:
                                st.error("Supabase client not initialized.")
                            
                        except Exception as e:
                            st.error(f"Upload failed: {e}")
                    else:
                        st.warning("Select an image.")

    st.divider()

    # --- STEP 2: DATA FETCHING (Always Fresh) ---
    # We fetch directly from DB to ensure we see what's actually there
    try:
        conn = get_connection()
        # Fetch only for current gender to optimize
        df_wardrobe = conn.query("SELECT * FROM wardrobe WHERE user_id=:uid AND gender=:gender", params={"uid": user_id, "gender": st.session_state.gender_mode}, ttl=0)
        
        # Update Session State Cache (Sync it)
        if not df_wardrobe.empty:
            st.session_state.wardrobe = df_wardrobe.to_dict('records')
        else:
            # If empty for this gender, we might still have other gender items in cache, so be careful.
            pass
            
    except Exception as e:
        st.error(f"Connection error: {e}")
        df_wardrobe = pd.DataFrame()

    # --- STEP 3: GRID DISPLAY & DELETE ---
    if not df_wardrobe.empty:
        # Group by Category
        categories_found = df_wardrobe['category'].unique()
        
        for cat in categories_found:
            st.markdown(f"### {cat}")
            cat_items = df_wardrobe[df_wardrobe['category'] == cat]
            
            cols = st.columns(4) # 4 columns for tighter grid
            for i, (index, row) in enumerate(cat_items.iterrows()):
                with cols[i % 4]:
                    # Card Container
                    with st.container(border=True):
                        # Display Image
                        if row['image_path'] and str(row['image_path']).startswith('http'):
                            st.image(row['image_path'], use_container_width=True)
                        else:
                            st.write("Image Missing")
                            
                        # Delete Button
                        if st.button("🗑️", key=f"del_reactive_{row['id']}", help="Delete Item"):
                            try:
                                # DB Delete
                                conn = get_connection()
                                with conn.session as s:
                                    s.execute(text("DELETE FROM wardrobe WHERE id=:id"), {"id": row['id']})
                                    s.commit()
                                
                                # Storage Delete (Best Effort)
                                if row['filename'] and supabase:
                                    try:
                                        bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
                                        supabase.storage.from_(bucket_name).remove([row['filename']])
                                    except: pass
                                    
                                st.toast("Deleted!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Delete failed: {e}")
    else:
        st.info(f"No {st.session_state.gender_mode} items yet.")

    # --- DANGER ZONE (Bulk Delete) ---
    st.markdown("---")
    with st.expander("🔴 Danger Zone"):
        st.warning(f"Permanently delete ALL **{st.session_state.gender_mode}** items.")
        if st.button(f"Delete All {st.session_state.gender_mode} Items", type="primary"):
            try:
                conn = get_connection()
                with conn.session as s:
                    s.execute(text("DELETE FROM wardrobe WHERE user_id=:uid AND gender=:g"), {"uid": user_id, "g": st.session_state.gender_mode})
                    s.commit()
                st.success("All deleted.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def save_item_to_wardrobe(image_file, category, gender):
    try:
        # 1. Image Processing (Compression)
        image = Image.open(image_file)
        
        # Convert to RGB (fixes RGBA issues with JPEG)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Resize (Max width 1000px)
        max_width = 1000
        if image.width > max_width:
            ratio = max_width / float(image.width)
            new_height = int(float(image.height) * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        # Save to BytesIO
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        # 2. Supabase Storage Upload
        if not supabase:
            return False
            
        bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
        
        file_ext = "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"{unique_filename}" # Path inside bucket
        
        supabase.storage.from_(bucket_name).upload(
            file_path,
            img_byte_arr.getvalue(),
            {"content-type": "image/jpeg"}
        )
        
        # 3. Get Public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        # 4. Database Insert
        new_id = str(uuid.uuid4())
        added_at = time.time()
        
        conn = get_connection()
        with conn.session as s:
            s.execute(
                text("INSERT INTO wardrobe (id, user_id, category, gender, image_path, filename, added_at) VALUES (:id, :user_id, :category, :gender, :image_path, :filename, :added_at)"),
                {"id": new_id, "user_id": 1, "category": category, "gender": gender, "image_path": public_url, "filename": unique_filename, "added_at": added_at}
            )
            s.commit()
            
            st.success("Item added to wardrobe!")
            time.sleep(1)
            st.rerun()
        
        # 5. Update Session State (This part won't be reached but kept for logic if rerun is removed)
        new_item = {
            "id": new_id,
            "category": category,
            "gender": gender,
            "image_path": public_url,
            "filename": unique_filename,
            "added_at": added_at
        }
        st.session_state.wardrobe.append(new_item)
        return True
    except Exception as e:
        st.error(f"Error saving item: {e}")
        return False

def delete_item_from_wardrobe(item_id, filename=None):
    try:
        # Step 1: DB Delete (Critical)
        conn = get_connection()
        with conn.session as s:
            s.execute(text("DELETE FROM wardrobe WHERE id=:id"), {"id": item_id})
            s.commit()
            
        # Step 2: Storage Delete (Fail-Safe)
        if filename and supabase:
            try:
                bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
                supabase.storage.from_(bucket_name).remove([filename])
            except:
                pass # Don't block if storage delete fails
        
        # Update session state cache
        st.session_state.wardrobe = [item for item in st.session_state.wardrobe if item['id'] != item_id]
        return True
    except Exception as e:
        st.error(f"Error deleting item: {e}")
        return False

@st.cache_data(ttl=60)
def get_wardrobe_items(user_id):
    # Use session state cache which is populated/updated
    items = []
    
    # Handle None user_id gracefully
    if user_id is None:
        return []

    # If cache is empty but DB might have items (startup), load them
    if not st.session_state.wardrobe:
        try:
            conn = get_connection()
            # Fetch ALL items for this user (Men's and Women's mixed)
            df = conn.query("SELECT * FROM wardrobe WHERE user_id=:uid", params={"uid": user_id}, ttl=0)
            
            loaded_items = []
            for index, row in df.iterrows():
                loaded_items.append({
                    "id": row['id'],
                    "category": row['category'],
                    "gender": row['gender'],
                    "image_path": row['image_path'],
                    "filename": row['filename'],
                    "added_at": row['added_at']
                })
            st.session_state.wardrobe = loaded_items
        except:
            pass

    if st.session_state.wardrobe:
        # Return ALL items from cache, no filtering
        items = st.session_state.wardrobe
            
    return items
`"; Add-Content developer_handover.md 
## modules/color.py
`python
import streamlit as st
from modules.chat import client, encode_image, extract_json_from_text

def display_color_swatches(color_list):
    # color_list is now a list of dicts: [{"name": "...", "hex": "..."}, ...]
    cols = st.columns(len(color_list))
    for i, color in enumerate(color_list):
        with cols[i]:
            st.markdown(f"""
            <div style="background-color: {color['hex']}; width: 100%; height: 60px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"></div>
            <p style="text-align:center; font-size: 0.8rem; margin-top: 5px;">{color['name']}</p>
            """, unsafe_allow_html=True)

def display_color_analysis():
    st.header("🎨 Personal Color Analysis")
    st.write("Upload a selfie to discover your seasonal color palette and find your power colors.")
    
    color_file = st.file_uploader("Upload a Selfie", type=["jpg", "jpeg", "png"], key="color_uploader")
    
    if color_file:
        st.image(color_file, width=300, caption="Your Selfie")
        
        if st.button("Find My Season", type="primary"):
            with st.spinner("Analyzing skin tone, eye color, and contrast..."):
                try:
                    base64_img = encode_image(color_file)
                    
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": '''You are a Master Color Analyst with expertise in the 12-Season Color System. 
                                    Analyze the skin tone (undertone), eye color, and hair contrast of the person in this photo. 
                                    Determine their specific Season (e.g., Deep Winter, Soft Autumn, Light Spring). 
                                    
                                    Return the result strictly as a JSON object with this structure:
                                    {
                                      "season_name": "Name of the Season Diagnosis",
                                      "reasoning": "A 2-sentence explanation of why this season was chosen based on their features.",
                                      "best_colors": [
                                         {"name": "Color Name 1", "hex": "#Hex1"},
                                         {"name": "Color Name 2", "hex": "#Hex2"},
                                         {"name": "Color Name 3", "hex": "#Hex3"},
                                         {"name": "Color Name 4", "hex": "#Hex4"},
                                         {"name": "Color Name 5", "hex": "#Hex5"}
                                      ],
                                      "avoid_colors": [
                                         {"name": "Bad Color 1", "hex": "#HexBad1"},
                                         {"name": "Bad Color 2", "hex": "#HexBad2"},
                                         {"name": "Bad Color 3", "hex": "#HexBad3"}
                                      ]
                                    }'''},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_img}",
                                        },
                                    },
                                ],
                            }
                        ],
                        temperature=0.5,
                        max_tokens=1000,
                        response_format={"type": "json_object"}
                    )
                    
                    result_text = response.choices[0].message.content
                    analysis = extract_json_from_text(result_text)
                    
                    if analysis:
                        st.session_state.user_season = analysis
                        st.rerun()
                    else:
                        st.error("Could not parse the analysis result. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error during analysis: {e}")

    if st.session_state.user_season:
        season_data = st.session_state.user_season
        
        st.divider()
        st.markdown(f'<div class="season-title">You are a {season_data.get("season_name", "Unknown Season")}</div>', unsafe_allow_html=True)
        st.write(f"**Reasoning:** {season_data.get('reasoning', '')}")
        
        st.subheader("✅ Your Power Colors")
        display_color_swatches(season_data.get("best_colors", []))
        
        st.subheader("❌ Colors to Avoid")
        display_color_swatches(season_data.get("avoid_colors", []))

        st.divider()
        st.info("💡 Want to see how these colors look on you?")
        if st.button("👉 Go to Virtual Try-On"):
            # Since we are using st.tabs, we can't easily switch tabs programmatically without a full reload or state hack.
            # For now, we will guide the user.
            st.toast("Please click the 'Virtual Try-On' tab at the top!", icon="✨")
            # Optional: If we want to force a reload to a specific state, we'd need to change how app.py handles tabs.
            # But the user request asked for: st.session_state.current_page = "Virtual Try-On"
            # We will set it just in case we add that logic later.
            st.session_state.current_page = "Virtual Try-On"
            st.rerun()
`"; Add-Content developer_handover.md 
