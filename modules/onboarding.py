import streamlit as st
from sqlalchemy import text
from modules import database

@st.dialog("Welcome to Outfyt AI")
def show_tutorial(user_id):
    st.markdown("### Your Personal AI Stylist Awaits! ✨")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🧥 Wardrobe", "📅 Planner", "🎨 Color Analysis"])
    
    with tab1:
        st.markdown("""
        #### 💬 Chat with your Stylist
        - **Ask Anything**: "What should I wear to a wedding?" or "Does this match?"
        - **Voice Mode**: Tap the microphone to speak naturally.
        - **Image Analysis**: Upload photos of clothes for instant feedback.
        """)
        st.image("https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80", caption="Get instant style advice.")

    with tab2:
        st.markdown("""
        #### 🧥 Digital Wardrobe
        - **Upload**: Add photos of your clothes to build your digital closet.
        - **Organize**: Categorize items by type (Tops, Bottoms, Shoes).
        - **Mix & Match**: The AI uses your wardrobe to create outfits.
        """)
        st.image("https://images.unsplash.com/photo-1558769132-cb1aea458c5e?auto=format&fit=crop&w=600&q=80", caption="Digitize your closet.")

    with tab3:
        st.markdown("""
        #### 📅 Outfit Planner
        - **Plan Ahead**: Schedule outfits for upcoming events.
        - **Smart Suggestions**: Let AI plan your week based on weather and style.
        - **Calendar View**: See your style journey at a glance.
        """)
        st.image("https://images.unsplash.com/photo-1506784983877-45594efa4cbe?auto=format&fit=crop&w=600&q=80", caption="Plan your look.")
        
    with tab4:
        st.markdown("""
        #### 🎨 Personal Color Analysis
        - **Discover Your Season**: Upload a selfie to find your seasonal color palette.
        - **Best Colors**: Learn which colors make you glow.
        - **Avoid**: Know which shades to stay away from.
        """)
        st.image("https://images.unsplash.com/photo-1502163140606-888448ae8cfe?auto=format&fit=crop&w=600&q=80", caption="Find your perfect colors.")

        st.divider()
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            try:
                database.supabase.table("user_profiles").update({"tutorial_completed": True}).eq("user_id", user_id).execute()
                st.session_state.tutorial_completed = True
                st.rerun()
            except Exception as e:
                st.error(f"Error saving progress: {e}")
