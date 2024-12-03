import streamlit as st
from Python_Files.translation_utils import translate_text
import time

# List of Indian states and UTs
INDIAN_STATES = [
    "Select your state",
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

# Language settings
LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "bn": "বাংলা",
    "te": "తెలుగు"
}

class BaseAgent:
    def __init__(self):
        self._is_loading = False

    def set_loading(self, state: bool):
        self._is_loading = state

    def is_loading(self) -> bool:
        return self._is_loading

    # Make sure any response processing clears the loading state
    async def process_response(self, response):
        try:
            return await self._process_response_impl(response)
        finally:
            self.set_loading(False)

def initialize_session_state():
    """Initialize all session state variables with separate contexts."""
    
    # First, handle the core persistent states
    if "core_state" not in st.session_state:
        st.session_state.core_state = {
            "user_state": "Select your state",
            "language": "en",
            "sidebar_state": "collapsed"
        }
    
    # Always sync user_state with core_state
    if "user_state" not in st.session_state:
        st.session_state.user_state = st.session_state.core_state["user_state"]
    else:
        # Update core_state if user_state has changed
        st.session_state.core_state["user_state"] = st.session_state.user_state
    
    # Always sync language with core_state
    if "language" not in st.session_state:
        st.session_state.language = st.session_state.core_state["language"]
    else:
        st.session_state.core_state["language"] = st.session_state.language
    
    # Always sync sidebar_state with core_state
    if "sidebar_state" not in st.session_state:
        st.session_state.sidebar_state = st.session_state.core_state["sidebar_state"]
    else:
        st.session_state.core_state["sidebar_state"] = st.session_state.sidebar_state
    
    # Initialize page-specific states only if they don't exist
    if "semantic_search" not in st.session_state:
        st.session_state.semantic_search = {
            "chat_history": [],
            "scheme_agent": None,
            "is_first_message": True
        }
    
    if "find_schemes" not in st.session_state:
        st.session_state.find_schemes = {
            "chat_history": [],
            "scheme_agent": None,
            "is_first_message": True,
            "current_question": 0,
            "user_responses": {},
            "questionnaire_completed": False
        }

def display_state_selector():
    """Display state selector in sidebar and handle state management."""
    with st.sidebar:
        st.header(translate_text("Your Location"))
        
        # Get current index from core_state
        current_index = INDIAN_STATES.index(st.session_state.core_state["user_state"]) if st.session_state.core_state["user_state"] in INDIAN_STATES else 0
        
        # Add a unique key for each page
        page_name = st.session_state.get('current_page', 'home')
        selector_key = f"state_selector_{page_name}"
        
        selected_state = st.selectbox(
            translate_text("Select your state"),
            options=INDIAN_STATES,
            index=current_index,
            key=selector_key
        )
        
        # Update both session state and core state if selection changes
        if selected_state != st.session_state.core_state["user_state"]:
            st.session_state.user_state = selected_state
            st.session_state.core_state["user_state"] = selected_state
            # Only reload if changing from or to "Select your state"
            if selected_state == "Select your state" or st.session_state.core_state["user_state"] == "Select your state":
                st.rerun()
        
        # Add language selector
        st.divider()
        current_lang_index = list(LANGUAGES.keys()).index(st.session_state.language)
        selected_lang = st.selectbox(
            "🌐 " + translate_text("Select Language"),
            options=list(LANGUAGES.values()),
            index=current_lang_index,
            key='lang_select'
        )
        
        # Update language if changed
        new_lang = list(LANGUAGES.keys())[list(LANGUAGES.values()).index(selected_lang)]
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            # Only reload if language actually changes
            if new_lang != st.session_state.core_state["language"]:
                st.session_state.core_state["language"] = new_lang
                st.rerun()
        
        return selected_state

def check_state_selection():
    """
    Check if user has selected a state and show prompt if not.
    Returns True if state is selected, False otherwise.
    """
    if st.session_state.core_state["user_state"] == "Select your state":
        st.warning("Please select your state from the sidebar to continue")
        return False
    return True

def get_greeting_message():
    """Returns a personalized greeting with clear instructions"""
    state = st.session_state.user_state
    
    # Simple chat message with instructions
    with st.chat_message("assistant"):
        st.write(f"Welcome! I'll help you find government schemes available in {state} and central schemes that you can benefit from.")
        st.write("You can ask me about: • Available schemes in your state • Eligibility criteria • Application process • Required documents • Benefits and features")