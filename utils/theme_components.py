import streamlit as st

def create_custom_theme():
    """Apply custom theme styling to the application."""
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 2rem;
            background-color: #f8f9fa;
        }
        
        /* Card styling */
        .stCard {
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin: 1rem 0;
            background: white;
            transition: transform 0.2s;
        }
        
        .stCard:hover {
            transform: translateY(-2px);
        }
        
        /* Button styling */
        .stButton>button {
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_chat_styles():
    """Apply chat-specific styles."""
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