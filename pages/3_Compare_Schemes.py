import streamlit as st
from utils.common import initialize_session_state, display_state_selector

st.set_page_config(
    page_title="Compare Schemes - RightScheme AI",
    page_icon="📊",
    layout="wide"
)

def main():
    initialize_session_state()
    
    st.title("📊 Compare Schemes")
    st.write("Compare different government schemes side by side.")
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    if st.session_state.user_state is None:
        st.info("👆 Please select your state from the sidebar to get started!")
        st.stop()
    
    st.write("This feature is coming soon!")
    
    # Placeholder content
    st.markdown("""
    ### Coming Soon!
    
    This section will allow you to:
    - Compare multiple schemes side by side
    - See detailed benefit comparisons
    - Understand eligibility differences
    - Make informed decisions about which schemes to apply for
    """)

if __name__ == "__main__":
    main() 