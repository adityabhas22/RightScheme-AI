import streamlit as st
from utils.common import initialize_session_state, display_state_selector, translate_text

def main():
    st.set_page_config(
        page_title="RightScheme AI",
        page_icon="🏛️",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Add state and language selector
    display_state_selector()
    
    st.title(translate_text("🏛️ Welcome to RightScheme AI"))
    
    st.markdown(translate_text("""
    ### Your Intelligent Guide to Government Schemes
    
    RightScheme AI helps citizens discover, understand, and access government welfare schemes 
    that are most relevant to them. Our platform combines advanced AI technology with 
    comprehensive scheme data to provide you with accurate, up-to-date information.
    
    ### Choose a Service:
    """))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(translate_text("### 🔍 Semantic Search"))
        st.write(translate_text("Ask questions about any government scheme and get detailed answers."))
        if st.button(translate_text("Go to Semantic Search"), use_container_width=True):
            st.switch_page("pages/1_Semantic_Search.py")
    
    with col2:
        st.info(translate_text("### 🎯 Find Right Scheme"))
        st.write(translate_text("Answer a few questions to discover schemes perfect for you."))
        if st.button(translate_text("Go to Find Right Scheme"), use_container_width=True):
            st.switch_page("pages/2_Find_Right_Scheme.py")
    
    with col3:
        st.info(translate_text("### 📊 Compare Schemes"))
        st.write(translate_text("Compare different schemes side by side to make informed decisions."))
        if st.button(translate_text("Go to Compare Schemes"), use_container_width=True):
            st.switch_page("pages/3_Compare_Schemes.py")

if __name__ == "__main__":
    main() 