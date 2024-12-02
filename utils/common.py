import streamlit as st
from Python_Files.translation_utils import translate_text

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

# Language settings
LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "bn": "বাংলা",
    "te": "తెలుగు"
}

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        "scheme_agent": None,
        "chat_history": [],
        "user_state": None,
        "is_first_message": True,
    }
    
    # Initialize language settings if not present
    if "language" not in st.session_state:
        st.session_state["language"] = "en"
    
    # Initialize other session state variables
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def display_state_selector():
    with st.sidebar:
        st.header(translate_text("Your Location"))
        
        # Get the current index
        current_index = 0
        if "user_state" in st.session_state and st.session_state.user_state:
            try:
                current_index = INDIAN_STATES.index(st.session_state.user_state)
            except ValueError:
                current_index = 0
        
        selected_state = st.selectbox(
            translate_text("Select your state"),
            options=INDIAN_STATES,
            index=current_index,
            key="state_selector"
        )
        
        if selected_state != "Select State":
            st.session_state.user_state = selected_state
            st.success(translate_text(f"Showing schemes available in {selected_state} and Central Schemes"))
        
        # Add language selector at the bottom of sidebar
        st.divider()
        
        # Language selector
        current_lang_index = list(LANGUAGES.keys()).index(st.session_state.language)
        selected_lang = st.selectbox(
            "🌐 " + translate_text("Select Language"),
            options=list(LANGUAGES.values()),
            index=current_lang_index,
            key='lang_select'
        )
        
        # Update language code when selection changes
        new_lang = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(selected_lang)]
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()  # Rerun to apply language change
        
        return selected_state