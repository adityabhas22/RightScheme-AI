import streamlit as st
from utils.common import initialize_session_state, display_state_selector
from Python_Files.scheme_agent import process_query, create_scheme_agent
from Python_Files.translation_utils import translate_text

st.set_page_config(
    page_title="Semantic Search - RightScheme AI",
    page_icon="🔍",
    layout="wide"
)

def display_thinking_animation():
    """Display a simple thinking text with fade animation."""
    thinking_text = translate_text("Thinking...")
    thinking_container = st.empty()
    with thinking_container.container():
        with st.chat_message("assistant"):
            st.markdown(f"""
                <div class="thinking-animation">{thinking_text}</div>
                <style>
                    .thinking-animation {{
                        animation: thinking 1.5s ease-in-out infinite;
                        color: #666;
                    }}
                    @keyframes thinking {{
                        0%, 100% {{ opacity: 0.3; }}
                        50% {{ opacity: 1; }}
                    }}
                </style>
            """, unsafe_allow_html=True)
    return thinking_container

def main():
    initialize_session_state()
    
    st.title(translate_text("🔍 Semantic Search"))
    st.write(translate_text("Ask me anything about Indian Government Schemes!"))
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    with st.sidebar:
        if st.button(translate_text("Clear Conversation")):
            st.session_state.chat_history = []
            st.session_state.scheme_agent = None
            st.session_state.is_first_message = True
            st.rerun()

    # Main chat interface
    if st.session_state.user_state is None:
        st.info(translate_text("👆 Please select your state from the sidebar to get started!"))
        st.stop()

    # Display welcome message for first-time users
    if st.session_state.is_first_message:
        welcome_message = translate_text(
            f"👋 Welcome! I'll help you find government schemes available in {st.session_state.user_state} "
            "and central schemes that you can benefit from."
        ) + "\n\n" + translate_text(
            "You can ask me about:"
        ) + "\n" + translate_text(
            "• Available schemes in your state\n"
            "• Eligibility criteria\n"
            "• Application process\n"
            "• Required documents\n"
            "• Benefits and features"
        )
        st.chat_message("assistant").write(welcome_message)

    # Display chat history with translations
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and st.session_state.language != "en":
                original_text = message["content"]
                translated_text = translate_text(original_text)
                
                # Display original English text
                st.write(original_text)
                
                # Only if language is not English, show translation
                if st.session_state.language != "en":
                    st.markdown("---")
                    st.markdown("**" + translate_text("Translation") + ":**")
                    st.write(translated_text)
            else:
                st.write(message["content"])

    # Chat input
    if prompt := st.chat_input(translate_text("Type your question here...")):
        if not st.session_state.chat_history:
            st.session_state.is_first_message = False
            
        # Process the query and update chat history in one go
        with st.chat_message("user"):
            st.write(prompt)
            
        # Show thinking animation
        thinking_container = display_thinking_animation()
        
        # Get response
        contextualized_query = f"For someone in {st.session_state.user_state}: {prompt}"
        response_data = process_query(contextualized_query)
        
        # Remove thinking animation
        thinking_container.empty()
        
        # Display response
        with st.chat_message("assistant"):
            # Store original English response
            original_response = response_data["response"]
            
            # Display original English first
            st.write(original_response)
            
            # Only if language is not English, show translation
            if st.session_state.language != "en":
                st.markdown("---")
                st.markdown("**" + translate_text("Translation") + ":**")
                st.write(translate_text(original_response))
        
        # Update chat history with original English response
        st.session_state.chat_history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": original_response}
        ])
        
        # Show conversation summary in sidebar
        with st.sidebar:
            with st.expander(translate_text("Conversation Summary"), expanded=False):
                if st.session_state.language != "en":
                    st.write(response_data["conversation_summary"])  # Original English
                    st.divider()
                    st.caption(translate_text("Translation:"))
                    st.write(translate_text(response_data["conversation_summary"]))  # Translated
                else:
                    st.write(response_data["conversation_summary"])

    # Add/modify the CSS for chat messages
    st.markdown("""
    <style>
        /* Base styles for chat messages */
        div.stChatMessage {
            padding: 1rem 1.5rem !important;
            margin: 0.5rem 0 !important;
            max-width: 80% !important;
            border-radius: 10px !important;
        }
        
        /* Assistant messages - left aligned */
        div.stChatMessage[data-testid="chat-message-assistant"] {
            margin-right: auto !important;
            margin-left: 1.5rem !important;
            background-color: #f0f2f6 !important;
        }
        
        /* User messages - right aligned */
        div.stChatMessage[data-testid="chat-message-user"] {
            margin-left: auto !important;
            margin-right: 1.5rem !important;
            background-color: #e3f2fd !important;
        }
        
        /* Optimize for mobile */
        @media (max-width: 768px) {
            div.stChatMessage {
                max-width: 90% !important;
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