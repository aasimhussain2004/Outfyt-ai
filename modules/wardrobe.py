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
