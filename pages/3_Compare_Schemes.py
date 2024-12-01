import streamlit as st
from utils.common import initialize_session_state, display_state_selector, translate_text

def main():
    initialize_session_state()
    
    st.title(translate_text("📊 Compare Schemes"))
    st.write(translate_text("Compare different government schemes side by side."))
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    if st.session_state.user_state is None:
        st.info(translate_text("👆 Please select your state from the sidebar to get started!"))
        st.stop()
    
    # Placeholder content
    st.markdown(translate_text("""
    ### Coming Soon!
    
    This section will allow you to:
    - Compare multiple schemes side by side
    - See detailed benefit comparisons
    - Understand eligibility differences
    - Make informed decisions about which schemes to apply for
    """))

if __name__ == "__main__":
    main() 