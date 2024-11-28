import streamlit as st
from utils.common import initialize_session_state, display_state_selector

st.set_page_config(
    page_title="Find Right Scheme - RightScheme AI",
    page_icon="🎯",
    layout="wide"
)

def main():
    initialize_session_state()
    
    st.title("🎯 Find Right Scheme")
    st.write("Answer a few questions to discover the perfect schemes for you.")
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    if st.session_state.user_state is None:
        st.info("👆 Please select your state from the sidebar to get started!")
        st.stop()
    
    st.write("This feature is coming soon!")
    
    # Placeholder content
    st.markdown("""
    ### Coming Soon!
    
    This section will help you:
    - Answer simple questions about your profile
    - Get personalized scheme recommendations
    - Find schemes that match your eligibility
    - Discover benefits you might not know about
    """)

if __name__ == "__main__":
    main() 