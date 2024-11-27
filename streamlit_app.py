import streamlit as st
from query_vectordb import VectorDBQuerier
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Government Schemes Assistant",
    page_icon="🏛️",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def initialize_querier():
    """Initialize the VectorDBQuerier instance"""
    vector_db_dir = os.path.join(os.path.dirname(__file__), "vectorDb")
    return VectorDBQuerier(vector_db_dir)

def display_chat_message(role, content, sources=None):
    """Display a chat message with optional sources"""
    with st.chat_message(role):
        st.write(content)
        if sources and role == "assistant":
            with st.expander("View Sources"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"""
                    **Source {i}**: {source['file']}  
                    **Relevance**: {source['relevance']:.4f}  
                    **Preview**: {source['text']}
                    """)

# Sidebar
with st.sidebar:
    st.title("🏛️ Government Schemes")
    st.markdown("""
    Get information about Indian Government Schemes:
    - Ask about eligibility criteria
    - Learn about benefits
    - Understand application processes
    """)
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.title("🤖 Government Schemes Assistant")

# Initialize querier
querier = initialize_querier()

# Display chat history
for message in st.session_state.messages:
    display_chat_message(
        message["role"],
        message["content"],
        message.get("sources")
    )

# Chat input
if prompt := st.chat_input("Ask about government schemes..."):
    # Display user message
    display_chat_message("user", prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get AI response
    results = querier.search(prompt, top_k=3)
    if results:
        response_data = querier.process_with_llm(prompt, results)
        
        # Display assistant message
        display_chat_message(
            "assistant",
            response_data["ai_response"],
            response_data["sources"]
        )
        
        # Save to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_data["ai_response"],
            "sources": response_data["sources"]
        })
    else:
        error_message = "I couldn't find relevant information for your query. Please try rephrasing your question."
        display_chat_message("assistant", error_message)
        st.session_state.messages.append({
            "role": "assistant",
            "content": error_message
        })

# Footer
st.markdown("---")
st.markdown("Powered by AI • Built for Indian Government Schemes") 