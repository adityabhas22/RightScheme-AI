import streamlit as st
from utils.common import initialize_session_state, display_state_selector, check_state_selection, get_greeting_message
from Python_Files.scheme_agent import process_query, create_scheme_agent
from Python_Files.translation_utils import translate_text
from utils.logging_utils import logger

st.set_page_config(
    page_title="Smart Search - RightScheme AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light mode
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF;
        }
        
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
        }
        
        [data-testid="stHeader"] {
            background-color: #FFFFFF;
        }
        
        .stButton button {
            background-color: #FFFFFF;
            color: #2C4875;
        }
        
        .stTextInput input {
            background-color: #FFFFFF;
        }
        
        .stSelectbox select {
            background-color: #FFFFFF;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Add after the page config
st.markdown("""
    <style>
        /* Global styles */
        [data-testid="stAppViewContainer"] {
            background-color: #F8FAFC;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        
        [data-testid="stSidebar"] h1 {
            color: #000000 !important;
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            padding: 1rem 0 0.5rem 0 !important;
        }
        
        [data-testid="stSidebar"] .stSelectbox label {
            color: #000000 !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stSidebar"] .stSelectbox > div > div {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 0.5rem !important;
            color: #000000 !important;
        }
        
        /* Chat interface styling */
        [data-testid="stChatMessage"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 0.75rem !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* User message styling */
        [data-testid="stChatMessage"][data-testid="user"] {
            background-color: #2C4875 !important;
            color: #FFFFFF !important;
        }
        
        [data-testid="stChatMessage"][data-testid="user"] p {
            color: #FFFFFF !important;
        }
        
        /* Assistant message styling */
        [data-testid="stChatMessage"][data-testid="assistant"] {
            background-color: #FFFFFF !important;
        }
        
        [data-testid="stChatMessage"][data-testid="assistant"] p {
            color: #2D3748 !important;
        }
        
        /* Input field styling */
        .stTextInput input {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 0.5rem !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            color: #2D3748 !important;
        }
        
        .stTextInput input:focus {
            border-color: #5785D9 !important;
            box-shadow: 0 0 0 2px rgba(87, 133, 217, 0.2) !important;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #2C4875 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton button:hover {
            background-color: #5785D9 !important;
            transform: translateY(-1px);
        }
        
        /* Thinking animation styling */
        .thinking-animation {
            color: #5785D9 !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            padding: 0.5rem 0 !important;
        }
        
        /* Search results styling */
        .search-result {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .search-result:hover {
            border-color: #5785D9;
            box-shadow: 0 4px 6px rgba(87, 133, 217, 0.1);
        }
        
        /* Headers and text */
        h1, h2, h3 {
            color: #2C4875 !important;
            font-weight: 600 !important;
        }
        
        
        
        /* Info messages */
        .stAlert {
            background-color: rgba(143, 184, 237, 0.1) !important;
            border: 1px solid #8FB8ED !important;
            color: #2C4875 !important;
            border-radius: 0.5rem !important;
        }
        
        /* Prevent link styling on hover */
        div[data-testid="stMarkdown"] div {
            pointer-events: none !important;
        }
        
        /* Only allow pointer events on actual buttons/links */
        a, .card-button, button {
            pointer-events: auto !important;
        }
    </style>
""", unsafe_allow_html=True)

# Update the search box styling
st.markdown("""
    <style>
        .search-container {
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(44, 72, 117, 0.1), 0 2px 4px -1px rgba(44, 72, 117, 0.06);
            border: 1px solid #E2E8F0;
            margin: 2rem 0;
        }
        
        .search-title {
            color: #2C4875;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

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
                        color: #5785D9;
                        font-weight: 500;
                        padding: 0.5rem 0;
                    }}
                    @keyframes thinking {{
                        0%, 100% {{ opacity: 0.5; }}
                        50% {{ opacity: 1; }}
                    }}
                </style>
            """, unsafe_allow_html=True)
    return thinking_container

def main():
    # Set current page for unique widget keys
    st.session_state['current_page'] = 'smart_search'
    
    initialize_session_state()
    display_state_selector()
    
    # Add semantic search icon styling
    st.markdown("""
        <style>
            .semantic-search-icon {
                width: 48px;
                height: 48px;
                margin: 0;
                display: inline-block;
                stroke: #2C4875;
                vertical-align: middle;
                margin-right: 1rem;
            }
            .title-container {
                display: flex;
                align-items: center;
                margin-bottom: 1rem;
            }
            .title-container h1 {
                display: inline;
                margin: 0;
            }
        </style>
        
        <div class="title-container">
            <svg class="semantic-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <h1>""" + translate_text("Semantic Search") + """</h1>
        </div>
    """, unsafe_allow_html=True)
    st.write(translate_text("Ask me anything about Indian Government Schemes!"))
    
    # Add reset button to sidebar
    with st.sidebar:
        if st.button(translate_text("Start New Search")):
            # Reset the chat history
            st.session_state.semantic_search = {
                "chat_history": [],
                "is_first_message": True
            }
            st.rerun()
    
    # Check state selection before proceeding
    if not check_state_selection():
        return
        
    # Display chat history
    if not st.session_state.semantic_search["chat_history"]:
        # Only add welcome message if chat history is empty
        welcome_msg = f"👋 Welcome! I'll help you find government schemes available in {st.session_state.user_state} and central schemes that you can benefit from.\n\nYou can ask me about: • Available schemes in your state • Eligibility criteria • Application process • Required documents • Benefits and features"
        st.session_state.semantic_search["chat_history"].append({"role": "assistant", "content": welcome_msg})
    
    # Display chat history - remove the container and columns
    for message in st.session_state.semantic_search["chat_history"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input(translate_text("Type your question here...")):
        if not st.session_state.semantic_search["chat_history"]:
            st.session_state.semantic_search["is_first_message"] = False
            
        # Process the query and update chat history in one go
        with st.chat_message("user"):
            st.write(prompt)
            
        # Show thinking animation
        thinking_container = display_thinking_animation()
        
        # Get response
        contextualized_query = f"For someone in {st.session_state.user_state}: {prompt}"
        response_data = process_query(contextualized_query)
        
        # Log the conversation
        logger.log_conversation(
            conversation_type="semantic_search",
            user_query=prompt,
            response=response_data["response"],
            metadata={
                "state": st.session_state.user_state,
                "language": st.session_state.language,
                "contextualized_query": contextualized_query
            }
        )
        
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
        
        # Update semantic search chat history
        st.session_state.semantic_search["chat_history"].extend([
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

    # Update the chat message styling
    st.markdown("""
        <style>
            /* Base styles for chat messages */
            div.stChatMessage {
                padding: 1rem 1.5rem !important;
                border-radius: 10px !important;
                border: 1px solid #E2E8F0 !important;
            }
            
            /* Assistant messages */
            div.stChatMessage[data-testid="chat-message-assistant"] {
                background-color: #FFFFFF !important;
                color: #2D3748 !important;
                box-shadow: 0 2px 4px rgba(44, 72, 117, 0.1) !important;
            }
            
            /* User messages */
            div.stChatMessage[data-testid="chat-message-user"] {
                background-color: #2C4875 !important;
                color: #FFFFFF !important;
            }
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 