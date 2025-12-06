import streamlit as st
import time

def show_tryon_page():
    st.header("✨ Virtual Try-On (Coming Soon)")
    st.caption("The Future of Your Digital Wardrobe")

    # Value Props
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 👔 Visualize Fit")
        st.write("See how clothes look on you before you buy.")
    with col2:
        st.markdown("### ⚡ Save Time")
        st.write("No more dressing room queues.")
    with col3:
        st.markdown("### 👗 Style Confidence")
        st.write("AI-powered fitting precision.")

    st.divider()

    # Mockup Comparison
    st.subheader("What to Expect")
    
    col_demo1, col_demo2 = st.columns(2)
    
    with col_demo1:
        st.markdown("**Before**")
        # Using a generic fashion image to represent input
        st.image("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=400&auto=format&fit=crop", caption="Your Photo + Garment", use_container_width=True)
    
    with col_demo2:
        st.markdown("**After (AI Result)**")
        # Using a high-quality fashion shot to represent the result
        st.image("https://images.unsplash.com/photo-1483985988355-763728e1935b?q=80&w=400&auto=format&fit=crop", caption="Perfect Virtual Fit", use_container_width=True)

    st.divider()

    # Call to Action
    st.info("We are fine-tuning our AI models to provide the best experience.")
    
    if st.button("🔔 Notify Me When Ready", type="primary", use_container_width=True):
        st.toast("You're on the list! We'll notify you soon.", icon="🎉")
        time.sleep(2)