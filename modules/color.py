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
