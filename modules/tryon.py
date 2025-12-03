import streamlit as st
import requests
import io
import time
from PIL import Image

# Placeholder for future API integration
# API_URL = "https://api-inference.huggingface.co/models/yisol/IDM-VTON"
# headers = {"Authorization": f"Bearer {st.secrets['HUGGINGFACE_TOKEN']}"}

def query_vton(person_img_bytes, garment_img_bytes):
    """
    Mock VTON function to simulate processing.
    In the future, this will call the HuggingFace Inference API.
    """
    # Simulate processing time
    time.sleep(3) 
    
    # Return the original person image as a placeholder result
    return Image.open(io.BytesIO(person_img_bytes))

def show_tryon_page():
    st.header("✨ Virtual Try-On")
    st.caption("Experience the future of fashion. See how clothes look on you before you buy.")

    # --- Premium Check ---
    if not st.session_state.get("is_premium", False):
        # --- FREE USER VIEW (Teaser) ---
        st.info("🔒 This is a Premium Feature")
        
        col1, col2 = st.columns(2)
        
        gender_mode = st.session_state.get("gender_mode", "Men's Fashion")
        
        with col1:
            st.markdown("### Before")
            if gender_mode == "Men's Fashion":
                # Placeholder for Men's example
                st.markdown("👔 **Men's Example**")
                st.image("https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=300&auto=format&fit=crop", caption="Original Photo")
                st.image("https://images.unsplash.com/photo-1596755094514-f87e34085b2c?q=80&w=300&auto=format&fit=crop", caption="Garment (Shirt)")
            else:
                # Placeholder for Women's example
                st.markdown("👗 **Women's Example**")
                st.image("https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=300&auto=format&fit=crop", caption="Original Photo")
                st.image("https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?q=80&w=300&auto=format&fit=crop", caption="Garment (Dress)")

        with col2:
            st.markdown("### After (AI Generated)")
            if gender_mode == "Men's Fashion":
                st.image("https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=300&auto=format&fit=crop", caption="Virtual Try-On Result (Mock)")
            else:
                st.image("https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=300&auto=format&fit=crop", caption="Virtual Try-On Result (Mock)")
            
            st.markdown("#### Why Upgrade?")
            st.write("✅ Unlimited Try-Ons")
            st.write("✅ High-Quality IDM-VTON Model")
            st.write("✅ Save Results to Wardrobe")

        st.divider()
        if st.button("🚀 Upgrade to Premium to Try It Yourself", type="primary", use_container_width=True):
            st.session_state.trigger_upgrade = True
            st.rerun()

    else:
        # --- PREMIUM USER VIEW (Functional) ---
        st.success("🔓 Premium Access Unlocked")
        
        col_upload1, col_upload2 = st.columns(2)
        
        with col_upload1:
            person_file = st.file_uploader("1. Upload Your Photo", type=["jpg", "jpeg", "png"], key="vton_person")
            if person_file:
                st.image(person_file, caption="You", width=200)

        with col_upload2:
            garment_file = st.file_uploader("2. Upload Garment Photo", type=["jpg", "jpeg", "png"], key="vton_garment")
            if garment_file:
                st.image(garment_file, caption="Garment", width=200)

        if person_file and garment_file:
            if st.button("✨ Generate Try-On", type="primary", use_container_width=True):
                with st.spinner("AI is dressing you up... (This may take a few seconds)"):
                    try:
                        # Convert to bytes
                        person_bytes = person_file.getvalue()
                        garment_bytes = garment_file.getvalue()
                        
                        # Call Mock API
                        result_image = query_vton(person_bytes, garment_bytes)
                        
                        st.divider()
                        st.subheader("🎉 Your Look")
                        st.image(result_image, caption="Virtual Try-On Result", use_container_width=True)
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
