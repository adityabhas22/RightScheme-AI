import streamlit as st
from Python_Files.translation_utils import (
    initialize_translation_settings,
    get_translation_selector,
    translate_text
)

# List of Indian states and UTs
INDIAN_STATES = [
    "Select State",
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

def initialize_session_state():
    if "scheme_agent" not in st.session_state:
        st.session_state.scheme_agent = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "user_state" not in st.session_state:
        st.session_state.user_state = None
    if "is_first_message" not in st.session_state:
        st.session_state.is_first_message = True

def main():
    st.set_page_config(
        page_title="Scheme Eligibility Checker",
        page_icon="🏠",
        layout="wide"
    )
    
    # Initialize translation settings
    initialize_translation_settings()
    
    # Add language selector to sidebar
    get_translation_selector()
    
    # Translate main title
    st.title(translate_text("Scheme Eligibility Checker"))
    
    # Rest of your main app code...
    welcome_text = """
    Welcome to the Scheme Eligibility Checker. This tool helps you find 
    government schemes you might be eligible for.
    """
    st.write(translate_text(welcome_text))
    
    # Continue with your existing app logic...

if __name__ == "__main__":
    main() 