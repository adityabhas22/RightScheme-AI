import streamlit as st
from typing import Dict, List
from utils.theme_utils import apply_chat_styles
from Python_Files.translation_utils import translate_text

def display_thinking_animation():
    """Display a thinking animation in chat."""
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

def display_chat_message(message: str, role: str = "assistant"):
    """Display a styled chat message."""
    with st.chat_message(role):
        st.write(message)

def display_bilingual_message(message: str, role: str):
    """Display message in both English and selected language."""
    with st.chat_message(role):
        # Always show English
        st.write(message)
        
        # Show translation if language is not English
        if st.session_state.language != "en":
            st.markdown("---")
            st.markdown(f"**{translate_text('Translation')}:**")
            st.write(translate_text(message))

def create_chat_input(placeholder: str = "Type your message..."):
    """Create a styled chat input field."""
    return st.chat_input(translate_text(placeholder))