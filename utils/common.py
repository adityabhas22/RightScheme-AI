import streamlit as st
from Python_Files.translation_utils import translate_text

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
    defaults = {
        # Shared state
        "user_state": "Select your state",
        "language": "en",
        
        # Semantic Search specific state
        "semantic_search": {
            "chat_history": [],
            "scheme_agent": None,
            "is_first_message": True
        },
        
        # Find Right Schemes specific state
        "find_schemes": {
            "chat_history": [],
            "scheme_agent": None,
            "is_first_message": True,
            "current_question": 0,
            "user_responses": {},
            "questionnaire_completed": False
        }
    }
    
    # Initialize each state variable if not present
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def display_state_selector():
    with st.sidebar:
        st.header(translate_text("Your Location"))
        
        # Get the current index
        current_index = INDIAN_STATES.index(st.session_state.user_state) if st.session_state.user_state in INDIAN_STATES else 0
        
        selected_state = st.selectbox(
            translate_text("Select your state"),
            options=INDIAN_STATES,
            index=current_index,
            key="state_selector"
        )
        
        # Update session state if selection changes
        if selected_state != st.session_state.user_state:
            st.session_state.user_state = selected_state
            if selected_state != "Select your state":
                st.success(translate_text(f"Showing schemes available in {selected_state} and Central Schemes"))
                st.rerun()  # Force a rerun to update all components
        
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