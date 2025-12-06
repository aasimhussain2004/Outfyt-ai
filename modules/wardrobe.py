import streamlit as st
import pandas as pd
import time
import uuid
import io
from PIL import Image
from modules.database import supabase, get_user_profile

def display_wardrobe():
    st.header("🧥 My Digital Wardrobe")
    st.write(f"Catalog your **{st.session_state.gender_mode}** items.")
    
    # --- STEP 1: UPLOAD SECTION (Reactive) ---
    MENS_CATEGORIES = ['Suit', 'Blazer', 'Shirt', 'T-Shirt', 'Trousers', 'Jeans', 'Shoes', 'Accessory']
    WOMENS_CATEGORIES = ['Dress', 'Saree', 'Lehenga', 'Top', 'Skirt', 'Jeans', 'Trousers', 'Heels', 'Accessory']
    current_categories = MENS_CATEGORIES if st.session_state.gender_mode == "Men's Fashion" else WOMENS_CATEGORIES

    with st.container():
        user_id = st.session_state.get("user_id", None) # Changed default to None for better handling

        # --- 0. GUEST CHECK ---
        if not st.session_state.get("is_signed_in", False):
            st.info("🔒 Sign In to build your digital wardrobe.")
            if st.button("Sign In to Upload", key="wardrobe_signin_btn"):
                st.session_state.temp_signin = True
                st.rerun()
            st.divider()
            # Fall through to show grid (read-only) or empty state
        
        # --- FREEMIUM CHECK ---
        # Note: We check limit inside save_item_to_wardrobe now, but for UI feedback we can check here too
        # or just let the user try to upload and fail if limit reached.
        # For better UX, let's show the limit status.
        
        is_premium = False
        if user_id:
            profile = get_user_profile(user_id)
            is_premium = profile.get("is_premium", False)
        
        # Count items
        total_count = 0
        mens_count = 0
        womens_count = 0
        try:
            if supabase and user_id:
                # Fetch all items to analyze distribution
                res_all = supabase.table("wardrobe").select("gender", count="exact").eq("user_id", str(user_id)).execute()
                total_count = res_all.count
                
                # Analyze distribution for breakdown message
                if res_all.data:
                    df_all = pd.DataFrame(res_all.data)
                    mens_count = len(df_all[df_all['gender'] == "Men's Fashion"])
                    womens_count = len(df_all[df_all['gender'] == "Women's Fashion"])
        except Exception as e:
            # st.error(f"Error counting items: {e}") # Debugging
            total_count = 0 # Assume 0 if error
            
        limit_reached = not is_premium and total_count >= 5
        
        if limit_reached:
            st.error(f"🚫 Total Wardrobe Limit Reached ({total_count}/5 items).")
            breakdown_msg = f"**Breakdown:** {mens_count} Men's, {womens_count} Women's."
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
                st.write(f"Premium Status: `{is_premium}`")
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
                        if save_item_to_wardrobe(wardrobe_file, category, st.session_state.gender_mode):
                            st.rerun()
                    else:
                        st.warning("Select an image.")

    st.divider()

    # --- STEP 2: DATA FETCHING ---
    wardrobe_items = get_wardrobe_items(user_id)
    
    # Filter by current gender mode for display
    current_mode_items = [item for item in wardrobe_items if item.get('gender') == st.session_state.gender_mode]

    # --- STEP 3: GRID DISPLAY & DELETE ---
    if current_mode_items:
        # Group by Category
        df = pd.DataFrame(current_mode_items)
        categories_found = df['category'].unique()
        
        for cat in categories_found:
            st.markdown(f"### {cat}")
            cat_items = df[df['category'] == cat]
            
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
                            if delete_item_from_wardrobe(row['id'], row.get('filename')):
                                st.toast("Deleted!")
                                time.sleep(0.5)
                                st.rerun()
    else:
        st.info(f"No {st.session_state.gender_mode} items yet.")

    # --- DEBUGGING (Temporary) ---
    with st.expander("🛠️ Debugging Tools (Wardrobe)"):
        st.write(f"**Current User ID:** `{user_id}`")
        st.write(f"**Current Mode:** `{st.session_state.gender_mode}`")
        st.write(f"**Raw Items Fetched:** {len(wardrobe_items)}")
        if wardrobe_items:
            st.json(wardrobe_items)
        else:
            st.warning("No items returned from DB for this User ID.")

    # --- DANGER ZONE (Bulk Delete) ---
    st.markdown("---")
    with st.expander("🔴 Danger Zone"):
        st.warning(f"Permanently delete ALL **{st.session_state.gender_mode}** items.")
        if st.button(f"Delete All {st.session_state.gender_mode} Items", type="primary"):
            try:
                if supabase and user_id:
                    # First, get filenames to delete from storage
                    items_to_delete = supabase.table("wardrobe").select("filename").eq("user_id", str(user_id)).eq("gender", st.session_state.gender_mode).execute()
                    filenames = [item['filename'] for item in items_to_delete.data if item['filename']]

                    # Then, delete from DB
                    supabase.table("wardrobe").delete().eq("user_id", str(user_id)).eq("gender", st.session_state.gender_mode).execute()
                    
                    # Finally, delete from storage
                    if filenames:
                        try:
                            bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
                            supabase.storage.from_(bucket_name).remove(filenames)
                        except Exception as storage_e:
                            st.warning(f"Could not delete all files from storage: {storage_e}")

                    st.success("All deleted.")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def save_item_to_wardrobe(image_file, category, gender):
    if not supabase:
        st.error("Database connection failed.")
        return False
        
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("User not found. Please sign in.")
        return False

    try:
        # Step A: Check Premium Status
        profile = get_user_profile(user_id)
        is_premium = profile.get("is_premium", False)
        
        # Step B: Check Limits (if not premium)
        if not is_premium:
            res = supabase.table("wardrobe").select("*", count="exact").eq("user_id", str(user_id)).execute()
            if res.count >= 5:
                st.error("Wardrobe limit reached (5 items). Upgrade to Premium to add more.")
                return False

        # 1. Image Processing (Compression)
        image = Image.open(image_file)
        if image.mode in ("RGBA", "P"): image = image.convert("RGB")
            
        max_width = 1000
        if image.width > max_width:
            ratio = max_width / float(image.width)
            new_height = int(float(image.height) * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        # 2. Supabase Storage Upload
        bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
        file_ext = "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"{unique_filename}"
        
        supabase.storage.from_(bucket_name).upload(
            file_path,
            img_byte_arr.getvalue(),
            {"content-type": "image/jpeg"}
        )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        # 3. Database Insert (Supabase)
        new_item = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "category": category,
            "gender": gender,
            "image_path": public_url,
            "filename": unique_filename,
            "added_at": time.time()
        }
        
        supabase.table("wardrobe").insert(new_item).execute()
        
        st.success("Item added to wardrobe!")
        
        # Update cache if exists
        if "wardrobe" in st.session_state and isinstance(st.session_state.wardrobe, list):
             st.session_state.wardrobe.append(new_item)
             
        return True
        
    except Exception as e:
        err_msg = str(e)
        if "invalid input syntax for type integer" in err_msg:
             st.error("🛑 Database Schema Error: The 'user_id' column in your 'wardrobe' table is set to Integer, but Google Login uses UUIDs (Text). Please change the column type to Text or UUID in Supabase.")
        else:
             st.error(f"Error saving item: {e}")
        return False

def delete_item_from_wardrobe(item_id, filename=None):
    if not supabase: return False
    
    try:
        # Step 1: DB Delete
        supabase.table("wardrobe").delete().eq("id", item_id).execute()
            
        # Step 2: Storage Delete
        if filename:
            try:
                bucket_name = st.secrets["SUPABASE_STORAGE_BUCKET"]
                supabase.storage.from_(bucket_name).remove([filename])
            except:
                pass # Don't block if storage delete fails
        
        # Update session state cache
        if "wardrobe" in st.session_state and isinstance(st.session_state.wardrobe, list):
            st.session_state.wardrobe = [item for item in st.session_state.wardrobe if item['id'] != item_id]
            
        return True
    except Exception as e:
        st.error(f"Error deleting item: {e}")
        return False

# @st.cache_data(ttl=60) # Removed caching to fix immediate update issue
def get_wardrobe_items(user_id):
    if not supabase or not user_id:
        return []

    try:
        response = supabase.table("wardrobe").select("*").eq("user_id", str(user_id)).execute()
        return response.data
    except Exception as e:
        # st.error(f"Error fetching wardrobe: {e}") # Uncomment for debugging
        return []
