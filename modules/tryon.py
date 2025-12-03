import streamlit as st
import os
import shutil
from gradio_client import Client, handle_file
from PIL import Image

# Global variable to store connection error
connection_error = None
client = None

# Initialize Client (uses free GPU space or your HF Token)
# We use the official IDM-VTON space
# Initialize Client (uses free GPU space or your HF Token)
# We use the official IDM-VTON space
try:
    # Debug Token
    hf_token = st.secrets.get("HUGGINGFACE_TOKEN", None)
    if hf_token:
        print("DEBUG: HUGGINGFACE_TOKEN Found")
    else:
        print("DEBUG: HUGGINGFACE_TOKEN Missing")

    try:
        # Try with token (Preferred for higher limits)
        client = Client("yisol/IDM-VTON", hf_token=hf_token)
    except TypeError:
        # Fallback for older library versions or API mismatch
        print("⚠️ Warning: gradio_client version might be incompatible with hf_token. Connecting without token.")
        client = Client("yisol/IDM-VTON")

except Exception as e:
    connection_error = str(e)
    print(f"Failed to initialize Gradio Client: {e}")
    client = None

def query_vton(person_img_path, garment_img_path):
    """
    Sends images to HuggingFace IDM-VTON Space and returns the result path.
    """
    if not client:
        return None, f"AI Client not connected. Error: {connection_error}"
        
    print(f"👕 Trying on: {garment_img_path} on {person_img_path}...")
    
    try:
        # The API signature for yisol/IDM-VTON typically accepts:
        # dict(background, layers...), garm_img, garment_des, is_checked, is_checked_crop, denoise_steps, seed
        
        # Note: We must handle file paths correctly for Gradio
        result = client.predict(
            dict={"background": handle_file(person_img_path), "layers": [], "composite": None},
            garm_img=handle_file(garment_img_path),
            garment_des="A cool fashion garment",
            is_checked=True, # Auto-crop? Yes.
            is_checked_crop=False, 
            denoise_steps=30,
            seed=42,
            api_name="/tryon"
        )
        
        # Result is usually a tuple of paths (output_img, mask_img)
        # We want the first one (the final output)
        output_path = result[0] 
        return output_path, None

    except Exception as e:
        error_msg = str(e)
        if "Queue" in error_msg or "busy" in error_msg.lower():
            return None, "⚠️ AI Server is busy (High Traffic). Please try again in 1 minute or Upgrade for dedicated GPU."
        return None, f"AI Processing Failed: {error_msg}"

def save_uploaded_file(uploaded_file):
    """
    Saves uploaded file to a temporary directory and returns the path.
    """
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

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
                st.markdown("👔 **Men's Example**")
                st.image("https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=300&auto=format&fit=crop", caption="Original Photo")
                st.image("https://images.unsplash.com/photo-1596755094514-f87e34085b2c?q=80&w=300&auto=format&fit=crop", caption="Garment (Shirt)")
            else:
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
                with st.spinner("AI is dressing you up... (This may take ~30-60 seconds)"):
                    try:
                        # Save files to temp
                        person_path = save_uploaded_file(person_file)
                        garment_path = save_uploaded_file(garment_file)
                        
                        # Call Real API
                        result_path, error = query_vton(person_path, garment_path)
                        
                        if error:
                            st.error(error)
                        else:
                            st.divider()
                            st.subheader("🎉 Your Look")
                            
                            # Center the image and limit width
                            col_res1, col_res2, col_res3 = st.columns([1, 2, 1])
                            with col_res2:
                                st.image(result_path, caption="✨ Your Virtual Try-On Result", width=350)
                            
                            st.balloons()
                            
                            # Clean up temp files (Optional, but good practice)
                            # os.remove(person_path)
                            # os.remove(garment_path)
                            
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
