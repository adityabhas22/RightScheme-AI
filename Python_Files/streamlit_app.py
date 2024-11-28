import streamlit as st
from scheme_agent import process_query, create_scheme_agent

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

st.set_page_config(
    page_title="Government Schemes Assistant",
    page_icon="🏛️",
    layout="wide"
)

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
    initialize_session_state()
    
    st.title("🏛️ Government Schemes Assistant")
    
    # State selection in sidebar
    with st.sidebar:
        st.header("Your Location")
        selected_state = st.selectbox(
            "Select your state",
            options=INDIAN_STATES,
            index=0,
            key="state_selector"
        )
        
        if selected_state != "Select State":
            st.session_state.user_state = selected_state
            st.success(f"Showing schemes available in {selected_state} and Central Schemes")
        
        if st.button("Clear Conversation"):
            st.session_state.chat_history = []
            st.session_state.scheme_agent = None
            st.session_state.is_first_message = True
            st.rerun()

    # Main chat interface
    if st.session_state.user_state is None:
        st.info("👆 Please select your state from the sidebar to get started!")
        st.stop()

    # Display welcome message for first-time users
    if st.session_state.is_first_message:
        welcome_message = (
            f"👋 Welcome! I'll help you find government schemes available in {st.session_state.user_state} "
            "and central schemes that you can benefit from.\n\n"
            "You can ask me about:\n"
            "• Available schemes in your state\n"
            "• Eligibility criteria\n"
            "• Application process\n"
            "• Required documents\n"
            "• Benefits and features"
        )
        st.chat_message("assistant").write(welcome_message)

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if query := st.chat_input("Type your question here..."):
        st.session_state.is_first_message = False
        
        # Add state context to the query
        contextualized_query = f"For someone in {st.session_state.user_state}: {query}"
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": query})

        # Get response
        with st.spinner("Thinking..."):
            response_data = process_query(contextualized_query)

        # Add assistant response to chat history
        st.session_state.chat_history.append(
            {"role": "assistant", "content": response_data["response"]}
        )

        # Show conversation summary in sidebar
        with st.sidebar:
            with st.expander("Conversation Summary", expanded=False):
                st.write(response_data["conversation_summary"])

        # Rerun to update chat display
        st.rerun()

if __name__ == "__main__":
    main() 