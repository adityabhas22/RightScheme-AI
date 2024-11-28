import streamlit as st
from utils.common import initialize_session_state, display_state_selector
from Python_Files.scheme_agent import process_query, create_scheme_agent

st.set_page_config(
    page_title="Semantic Search - RightScheme AI",
    page_icon="🔍",
    layout="wide"
)

def main():
    initialize_session_state()
    
    st.title("🔍 Semantic Search")
    st.write("Ask me anything about Indian Government Schemes!")
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    with st.sidebar:
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

    # Add/modify the CSS for chat messages
    st.markdown("""
    <style>
        /* Optimize message containers for mobile */
        div.stChatMessage {
            padding: 1rem 1.5rem !important;
            margin: 0.5rem 0 !important;
            max-width: 100% !important;
        }
        
        /* Reduce indentation on mobile */
        @media (max-width: 768px) {
            div.stChatMessage {
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            
            div.stChatMessage [data-testid="chatAvatarIcon-user"],
            div.stChatMessage [data-testid="chatAvatarIcon-assistant"] {
                padding: 0 !important;
            }
            
            div.stChatMessage [data-testid="StMarkdownContainer"] {
                margin-left: 0.5rem !important;
                margin-right: 0.5rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 