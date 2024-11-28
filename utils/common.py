import streamlit as st

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

def display_state_selector():
    with st.sidebar:
        st.header("Your Location")
        
        # Get the current index
        current_index = 0
        if "user_state" in st.session_state and st.session_state.user_state:
            try:
                current_index = INDIAN_STATES.index(st.session_state.user_state)
            except ValueError:
                current_index = 0
        
        selected_state = st.selectbox(
            "Select your state",
            options=INDIAN_STATES,
            index=current_index,
            key="state_selector"
        )
        
        if selected_state != "Select State":
            st.session_state.user_state = selected_state
            st.success(f"Showing schemes available in {selected_state} and Central Schemes")
        
        return selected_state