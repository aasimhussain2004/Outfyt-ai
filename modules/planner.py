import streamlit as st
import datetime
from datetime import timedelta
import json
import time
import pandas as pd
import random
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
# from duckduckgo_search import DDGS # Removed in favor of Tavily
from groq import Groq
from modules.database import supabase
from modules.wardrobe import get_wardrobe_items

# Initialize Groq Client
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    client = None

def display_outfit_planner():
    st.header("📅 Outfit Planner")
    st.write("Schedule your looks for the week ahead.")
    
    col_scheduler, col_week = st.columns([1, 2])
    
    with col_scheduler:
        st.subheader("✨ Smart Planner")
        
        with st.form("smart_planner_form"):
            occasion = st.selectbox("Occasion", ["Office/Work", "Party/Night", "Vacation", "Casual/Weekend"])
            num_days = st.slider("Days to Plan", 1, 7, 5)
            st.caption("Plan starts from tomorrow.")
            
            c_gen, c_clear = st.columns([2, 1])
            with c_gen:
                if st.form_submit_button("✨ Generate Plan", type="primary", use_container_width=True):
                    with st.spinner("AI is styling your week..."):
                        success, msg = generate_smart_plan(occasion, num_days)
                        if success:
                            st.success(f"Plan generated for {occasion}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed: {msg}")
            with c_clear:
                if st.form_submit_button("🗑️ Clear All", type="secondary", use_container_width=True):
                    clear_all_plans()
                    st.rerun()
        
        st.divider()
        st.caption("Manual Override")
        with st.expander("Manually Plan a Day"):
            # Session State Fix: Ensure stored date is not in the past
            today = datetime.date.today()
            if "manual_date" in st.session_state:
                if st.session_state.manual_date < today:
                    st.session_state.manual_date = today

            plan_date = st.date_input("Select Date", min_value=today, key="manual_date")
            date_str = plan_date.strftime("%Y-%m-%d")
            
            # Dynamic Dropdowns based on Gender Mode
            current_mode = st.session_state.gender_mode
            
            if current_mode == "Men's Fashion":
                cats_to_plan = ["Suit", "Shirt", "Trousers", "Shoes"]
            else:
                cats_to_plan = ["Dress", "Top", "Skirt", "Trousers", "Heels"]
                
            selected_outfit = {}
            
            with st.form("manual_planner_form"):
                # 1. Fetch ALL items for this user (Fixing TypeError at 1812)
                current_user_id = st.session_state.get("user_id", 1)
                all_items_list = get_wardrobe_items(current_user_id)
                all_items_df = pd.DataFrame(all_items_list) if all_items_list else pd.DataFrame()

                for cat in cats_to_plan:
                    # 2. Filter Client-Side
                    items = []
                    if not all_items_df.empty and 'gender' in all_items_df.columns and 'category' in all_items_df.columns:
                        # Filter for current mode AND current category
                        mask = (all_items_df['gender'] == current_mode) & (all_items_df['category'] == cat)
                        items = all_items_df[mask].to_dict('records')

                    options = {item['id']: f"{item['category']} (Added {datetime.datetime.fromtimestamp(item['added_at']).strftime('%m/%d')})" for item in items}
                    
                    selected_id = st.selectbox(f"Select {cat}", options=list(options.keys()), format_func=lambda x: options[x], key=f"plan_{cat}", index=None, placeholder="Choose an item...")
                    if selected_id:
                        selected_outfit[cat] = selected_id
                
                if st.form_submit_button("Save Manual Look"):
                    if selected_outfit:
                        if save_plan(date_str, selected_outfit):
                            st.success(f"Outfit saved for {plan_date.strftime('%A, %b %d')}!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("Please select at least one item.")

    with col_week:
        st.subheader("Your Week Ahead")
        
        today = datetime.date.today()
        for i in range(5):
            day = today + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_display = day.strftime("%A, %b %d")
            
            plan = get_plan(day_str)
            
            # Gender Leakage Fix: Skip plans not for current mode
            if plan and plan.get('gender') != st.session_state.gender_mode:
                plan = None

            st.markdown(f"**{day_display}**")
            
            if plan:
                # Card Style
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1);">
                    <h4 style="margin-top:0;">{day_display}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Filter out 'gender' and 'note' keys from display loop
                display_items = {k: v for k, v in plan.items() if k not in ['gender', 'note']}
                cols = st.columns(len(display_items))
                idx = 0
                for cat, item_id in display_items.items():
                    item = next((it for it in st.session_state.wardrobe if it['id'] == item_id), None)
                    if item and item.get('image_path'):
                        with cols[idx]:
                            st.image(item['image_path'], caption=cat, use_container_width=True)
                        idx += 1
                
                # Style Note
                if 'note' in plan:
                    st.info(f"💡 **Style Note:** {plan['note']}")
                
                # Actions
                c_shuf, c_dl, c_rem = st.columns([1, 1, 1])
                with c_shuf:
                    if st.button("🔄 Shuffle", key=f"shuf_{day_str}", use_container_width=True):
                        with st.spinner("Mixing it up..."):
                            shuffle_day_plan(day_str, "Casual") 
                            st.rerun()
                            
                with c_dl:
                    if st.button("🎨 Customize Story", key=f"cust_{day_str}", use_container_width=True):
                        story_studio_dialog(plan, day_display)
                
                with c_rem:
                    if st.button("❌ Remove", key=f"rem_{day_str}", use_container_width=True):
                        delete_plan_day(day_str)
                        st.rerun()
                
                st.markdown("---")
            else:
                st.markdown(f"<div style='padding:10px; background:rgba(255,255,255,0.05); border-radius:10px; color:#888; margin-bottom:10px;'>No outfit planned</div>", unsafe_allow_html=True)

def save_plan(date_str, outfit_dict):
    try:
        if not supabase: return False
        
        # Add gender to the plan
        outfit_dict['gender'] = st.session_state.gender_mode
        user_id = st.session_state.get("user_id", 1)
        
        data = {
            "date": date_str,
            "user_id": str(user_id),
            "outfit_data": json.dumps(outfit_dict)
        }
        
        # Upsert into Supabase
        supabase.table("planner").upsert(data).execute()
        
        # Update session state cache
        if "planner" not in st.session_state:
            st.session_state.planner = {}
        st.session_state.planner[date_str] = outfit_dict
        return True
    except Exception as e:
        st.error(f"Error saving plan: {e}")
        return False

def get_plan(date_str):
    # Try cache first
    if "planner" in st.session_state and date_str in st.session_state.planner:
        return st.session_state.planner[date_str]
        
    try:
        if not supabase: return None
        
        user_id = st.session_state.get("user_id", 1)
        response = supabase.table("planner").select("outfit_data").eq("date", date_str).eq("user_id", str(user_id)).execute()
        
        if response.data:
            plan = json.loads(response.data[0]['outfit_data'])
            if "planner" not in st.session_state:
                st.session_state.planner = {}
            st.session_state.planner[date_str] = plan
            return plan
        return None
    except:
        return None

from modules.search import search_tavily

def search_fashion_items(keywords):
    return search_tavily(keywords)

def extract_shopping_keywords(text):
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": 'You are a search query generator. Output a JSON object with a single key "query". The value must be a concise product name based on the user\'s last request. Example: {"query": "Men Black Oxford Shoes"}. Do not add conversational text.'},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=50,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content
    except Exception as e:
        return json.dumps({"query": text[:50]}) # Fallback JSON

def generate_aesthetic_story(outfit_dict, date_str, layout, background, filter_effect):
    try:
        # 1. Canvas Setup
        width, height = 1080, 1920
        
        # Background Logic
        if background == "Solid Dark":
            img = Image.new('RGB', (width, height), (14, 17, 23))
        elif background == "Deep Navy":
            img = Image.new('RGB', (width, height), (10, 10, 30))
        elif background == "Midnight Noise":
            img = Image.new('RGB', (width, height), (5, 5, 10))
            noise = Image.effect_noise((width, height), 20).convert('RGB')
            img = Image.blend(img, noise, 0.15)
        elif background == "Marble White":
            img = Image.new('RGB', (width, height), (245, 245, 245))
            # Simple marble-like noise
            noise = Image.effect_noise((width, height), 5).convert('RGB')
            img = Image.blend(img, noise, 0.05)
        elif background == "Sunset Blur":
            img = Image.new('RGB', (width, height), (50, 20, 40))
            draw = ImageDraw.Draw(img)
            draw.ellipse((-200, -200, 1000, 1000), fill=(255, 100, 50), outline=None)
            draw.ellipse((200, 800, 1400, 2000), fill=(100, 20, 150), outline=None)
            img = img.filter(ImageFilter.GaussianBlur(150))
        elif background == "Aura Gradient (Blue/Purple)":
            img = Image.new('RGB', (width, height), (20, 10, 40))
            draw = ImageDraw.Draw(img)
            draw.ellipse((-200, -200, 800, 800), fill=(50, 20, 100), outline=None)
            draw.ellipse((400, 1000, 1400, 2000), fill=(20, 50, 120), outline=None)
            img = img.filter(ImageFilter.GaussianBlur(100))
        elif background == "Retro Grain":
            img = Image.new('RGB', (width, height), (40, 40, 40))
            noise = Image.effect_noise((width, height), 20).convert('RGB')
            img = Image.blend(img, noise, 0.1)
        else:
            img = Image.new('RGB', (width, height), (14, 17, 23))

        draw = ImageDraw.Draw(img)
        
        # 2. Fonts
        try:
            font_vibe = ImageFont.truetype("arial.ttf", 40)
            font_watermark = ImageFont.truetype("arial.ttf", 30)
        except:
            font_vibe = ImageFont.load_default()
            font_watermark = ImageFont.load_default()

        # 3. Load Images
        images = []
        for cat, item_id in outfit_dict.items():
            if cat in ['gender', 'note']: continue
            item = next((it for it in st.session_state.wardrobe if it['id'] == item_id), None)
            if item and item.get('image_path'):
                try:
                    img_path = item['image_path']
                    if str(img_path).startswith('http'):
                        response = requests.get(img_path, timeout=5)
                        p_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
                    elif os.path.exists(img_path):
                        p_img = Image.open(img_path).convert("RGBA")
                    else:
                        continue

                    
                    # Apply Filters
                    if filter_effect == "B&W Moody":
                        p_img = ImageOps.grayscale(p_img).convert("RGBA")
                        enhancer = ImageEnhance.Contrast(p_img)
                        p_img = enhancer.enhance(1.2)
                    elif filter_effect == "B&W High Contrast":
                        p_img = ImageOps.grayscale(p_img).convert("RGBA")
                        enhancer = ImageEnhance.Contrast(p_img)
                        p_img = enhancer.enhance(1.5)
                    elif filter_effect == "Warm Glow":
                        overlay = Image.new('RGBA', p_img.size, (255, 200, 150, 50))
                        p_img = Image.alpha_composite(p_img, overlay)
                    elif filter_effect == "Cool & Sharp":
                        overlay = Image.new('RGBA', p_img.size, (200, 220, 255, 40))
                        p_img = Image.alpha_composite(p_img, overlay)
                        enhancer = ImageEnhance.Sharpness(p_img)
                        p_img = enhancer.enhance(1.5)
                    elif filter_effect == "Vintage Grain":
                        enhancer = ImageEnhance.Color(p_img)
                        p_img = enhancer.enhance(0.8) # Desaturate slightly
                        # Add slight yellow tint
                        overlay = Image.new('RGBA', p_img.size, (255, 240, 200, 30))
                        p_img = Image.alpha_composite(p_img, overlay)
                        
                    images.append(p_img)
                except:
                    pass
        
        if not images: return None
        
        num_imgs = len(images)

        # 4. Layout Logic
        # Define safe area (padding)
        pad = 50
        safe_width = width - 2*pad
        safe_height = height - 300 # Leave space for bottom text
        start_y = 100
        
        if layout == "Auto-Grid (Smart)":
            if num_imgs == 1:
                # Full center
                target_size = (safe_width, int(safe_height * 0.8))
                img1 = ImageOps.fit(images[0], target_size, method=Image.BICUBIC)
                img.paste(img1, (pad, start_y))
                
            elif num_imgs == 2:
                # Top/Bottom Split
                h_split = safe_height // 2 - 10
                target_size = (safe_width, h_split)
                
                img1 = ImageOps.fit(images[0], target_size, method=Image.BICUBIC)
                img2 = ImageOps.fit(images[1], target_size, method=Image.BICUBIC)
                
                img.paste(img1, (pad, start_y))
                img.paste(img2, (pad, start_y + h_split + 20))
                
            elif num_imgs == 3:
                # Magazine Layout: Left Half (Full), Right Half (Split)
                w_split = safe_width // 2 - 10
                h_full = safe_height
                h_half = safe_height // 2 - 10
                
                # Image 1 (Left, Full)
                img1 = ImageOps.fit(images[0], (w_split, h_full), method=Image.BICUBIC)
                img.paste(img1, (pad, start_y))
                
                # Image 2 (Right Top)
                img2 = ImageOps.fit(images[1], (w_split, h_half), method=Image.BICUBIC)
                img.paste(img2, (pad + w_split + 20, start_y))
                
                # Image 3 (Right Bottom)
                img3 = ImageOps.fit(images[2], (w_split, h_half), method=Image.BICUBIC)
                img.paste(img3, (pad + w_split + 20, start_y + h_half + 20))
                
            elif num_imgs >= 4:
                # Quad Grid
                w_half = safe_width // 2 - 10
                h_half = safe_height // 2 - 10
                
                coords = [
                    (pad, start_y),
                    (pad + w_half + 20, start_y),
                    (pad, start_y + h_half + 20),
                    (pad + w_half + 20, start_y + h_half + 20)
                ]
                
                for i in range(4):
                    if i < len(images):
                        p_img = ImageOps.fit(images[i], (w_half, h_half), method=Image.BICUBIC)
                        img.paste(p_img, coords[i])

        elif layout == "Vertical Stack":
            # Simple vertical stack
            h_slot = (safe_height // num_imgs) - 20
            current_y = start_y
            for p_img in images:
                p_img_resized = ImageOps.fit(p_img, (safe_width, h_slot), method=Image.BICUBIC)
                img.paste(p_img_resized, (pad, current_y))
                current_y += h_slot + 20

        elif layout == "Polaroid Scatter":
            # Random scatter logic (simplified for stability)
            centers = []
            if num_imgs == 2: centers = [(width//2, 600), (width//2, 1200)]
            elif num_imgs == 3: centers = [(width//2 - 100, 500), (width//2 + 100, 900), (width//2 - 50, 1300)]
            elif num_imgs >= 4: centers = [(width//3, 500), (2*width//3, 500), (width//3, 1100), (2*width//3, 1100)]
            else: centers = [(width//2, 900)]
            
            for i, p_img in enumerate(images):
                if i >= len(centers): break
                
                # Resize for polaroid
                p_img.thumbnail((600, 600))
                
                # Create Frame
                frame_w, frame_h = p_img.width + 40, p_img.height + 100
                frame = Image.new('RGBA', (frame_w, frame_h), (255, 255, 255, 255))
                frame.paste(p_img, (20, 20), p_img)
                
                # Rotate
                angle = random.randint(-10, 10)
                frame = frame.rotate(angle, expand=True, resample=Image.BICUBIC)
                
                cx, cy = centers[i]
                x = cx - frame.width // 2
                y = cy - frame.height // 2
                
                # Paste with mask for transparency
                img.paste(frame, (x, y), frame)

        # 5. Text Overlays
        # Vibe Check
        vibe_text = "Vibe: Clean • Minimal • Sharp" # Placeholder logic
        w_vibe = draw.textlength(vibe_text, font=font_vibe)
        draw.text(((width - w_vibe) // 2, height - 150), vibe_text, fill="#FFFFFF", font=font_vibe)
        
        # Watermark
        watermark_text = "Styled by Outfyt AI"
        w_wm = draw.textlength(watermark_text, font=font_watermark)
        draw.text(((width - w_wm) // 2, height - 60), watermark_text, fill="#AAAAAA", font=font_watermark)
        
        # 6. Output
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Error generating story: {e}")
        return None

@st.dialog("Aesthetic Story Studio")
def story_studio_dialog(plan, day_display):
    st.write("Customize your OOTD Story vibe.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        layout = st.selectbox("Layout", ["Auto-Grid (Smart)", "Polaroid Scatter", "Vertical Stack"])
    with c2:
        bg = st.selectbox("Background", ["Solid Dark", "Deep Navy", "Midnight Noise", "Marble White", "Sunset Blur", "Aura Gradient (Blue/Purple)", "Retro Grain"])
    with c3:
        filt = st.selectbox("Filter", ["None", "Warm Glow", "Cool & Sharp", "Vintage Grain", "B&W Moody", "B&W High Contrast"])
        
    if st.button("🔄 Refresh Preview", use_container_width=True):
        st.rerun()
        
    # Generate Preview
    with st.spinner("Creating aesthetic..."):
        story_buf = generate_aesthetic_story(plan, day_display, layout, bg, filt)
        
    if story_buf:
        st.image(story_buf, caption="Preview", use_container_width=True)
        st.download_button(
            label="✨ Download Story",
            data=story_buf,
            file_name=f"ootd_story.png",
            mime="image/png",
            type="primary",
            use_container_width=True
        )

def delete_plan_day(date_str):
    try:
        if not supabase: return False
        
        user_id = st.session_state.get("user_id", 1)
        supabase.table("planner").delete().eq("date", date_str).eq("user_id", str(user_id)).execute()
        
        # Update cache
        if date_str in st.session_state.planner:
            del st.session_state.planner[date_str]
        return True
    except Exception as e:
        st.error(f"Error deleting plan: {e}")
        return False

def clear_all_plans():
    try:
        if not supabase: return False
        
        user_id = st.session_state.get("user_id", 1)
        supabase.table("planner").delete().eq("user_id", str(user_id)).execute()
        
        # Clear cache
        st.session_state.planner = {}
        return True
    except Exception as e:
        st.error(f"Error clearing plans: {e}")
        return False

def generate_smart_plan(occasion, num_days):
    try:
        # 1. Get Wardrobe
        all_items = [item for item in st.session_state.wardrobe if item.get('gender', "Men's Fashion") == st.session_state.gender_mode]
        
        if not all_items:
            return False, "Wardrobe is empty!"

        # 2. Prepare Prompt
        items_json = json.dumps([{k: v for k, v in item.items() if k in ['id', 'category']} for item in all_items])
        
        system_prompt = f"""
        You are a Smart Stylist. Create a {num_days}-day outfit plan for a "{occasion}" occasion.
        
        Wardrobe: {items_json}
        
        Rules:
        1. Select a Top, Bottom, and Shoes for each day.
        2. Prioritize items strictly matching the occasion.
        3. FALLBACK LOGIC: If you run out of perfect matches, use the next best appropriate item.
        4. REASONING: For each day, provide a "style_reasoning" explaining why you chose this outfit (e.g., "Linen shirt for breathability").
        5. Variety: Try not to repeat the exact same outfit.
        6. Return JSON: {{ "Day 1": {{ "Top": "id", "Bottom": "id", "Shoes": "id", "style_reasoning": "..." }}, ... }}
        """
        
        start_date = datetime.date.today() + timedelta(days=1)
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Plan for {num_days} days starting {start_date}."}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        plan_json = json.loads(completion.choices[0].message.content)
        
        # 3. Save to DB
        current_date = start_date
        for day_key, outfit in plan_json.items():
            date_str = current_date.strftime("%Y-%m-%d")
            
            final_outfit = {}
            if "style_reasoning" in outfit:
                final_outfit["note"] = outfit["style_reasoning"]
            elif "note" in outfit:
                final_outfit["note"] = outfit["note"]
                
            for part in ["Top", "Bottom", "Shoes"]:
                item_id = outfit.get(part)
                if item_id:
                    found = next((it for it in all_items if it['id'] == item_id), None)
                    if found:
                        final_outfit[found['category']] = item_id
            
            save_plan(date_str, final_outfit)
            current_date += timedelta(days=1)
            
        return True, "Plan generated!"
        
    except Exception as e:
        return False, str(e)

def shuffle_day_plan(date_str, occasion):
    try:
        # Similar to generate but for 1 day
        all_items = [item for item in st.session_state.wardrobe if item.get('gender', "Men's Fashion") == st.session_state.gender_mode]
        items_json = json.dumps([{k: v for k, v in item.items() if k in ['id', 'category']} for item in all_items])
        
        system_prompt = f"""
        Pick a completely NEW outfit for "{occasion}" from this wardrobe.
        Wardrobe: {items_json}
        Return JSON: {{ "Top": "id", "Bottom": "id", "Shoes": "id", "note": "Refreshed look" }}
        """
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.9, # Higher temp for variety
            response_format={"type": "json_object"}
        )
        
        outfit = json.loads(completion.choices[0].message.content)
        
        final_outfit = {}
        if "note" in outfit:
            final_outfit["note"] = outfit["note"]
            
        for part in ["Top", "Bottom", "Shoes"]:
            item_id = outfit.get(part)
            if item_id:
                found = next((it for it in all_items if it['id'] == item_id), None)
                if found:
                    final_outfit[found['category']] = item_id
                    
        save_plan(date_str, final_outfit)
        return True
    except:
        return False
