import streamlit as st
from query_vectordb import VectorDBQuerier
import os

# Configure Streamlit page
st.set_page_config(
    page_title="RightScheme AI",
    page_icon="🏛️",
    layout="wide"
)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "initial_options"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "querier" not in st.session_state:
    vector_db_dir = os.path.join(os.path.dirname(__file__), "vectorDb")
    st.session_state.querier = VectorDBQuerier(vector_db_dir)

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

def show_initial_options():
    st.title("Welcome to RightScheme AI")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Semantic Search", use_container_width=True, 
                    help="Get instant answers about government schemes through our AI assistant"):
            st.session_state.current_page = "semantic_search"
            st.rerun()
    
    with col2:
        if st.button("Find Right Schemes", use_container_width=True,
                    help="Answer a few questions to discover schemes perfect for you"):
            st.session_state.current_page = "find_schemes"
            st.rerun()
    
    with col3:
        if st.button("Compare Schemes", use_container_width=True,
                    help="Compare different schemes side by side"):
            st.session_state.current_page = "compare_schemes"
            st.rerun()

def show_semantic_search():
    # Sidebar
    with st.sidebar:
        st.title("🏛️ Government Schemes")
        st.markdown("""
        Get information about Indian Government Schemes:
        - Ask about eligibility criteria
        - Learn about benefits
        - Understand application processes
        """)
        
        if st.button("← Back to Options"):
            st.session_state.current_page = "initial_options"
            st.rerun()
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
            # Reset the querier's memory
            st.session_state.querier.memory.clear()
            st.rerun()
        
        # Add conversation history viewer in sidebar
        with st.expander("View Conversation Summary"):
            st.write(st.session_state.querier.get_conversation_summary())
    
    # Main chat interface
    st.title("🤖 Government Schemes Assistant")
    
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
        results = st.session_state.querier.search(prompt, top_k=3)
        if results:
            response_data = st.session_state.querier.process_with_llm(prompt, results)
            
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
        st.rerun()

def show_find_schemes():
    # Back button in sidebar
    with st.sidebar:
        if st.button("← Back to Options"):
            st.session_state.current_page = "initial_options"
            st.rerun()
    
    st.title("Find Right Schemes")
    
    # Placeholder UI for Find Schemes
    st.info("This feature is coming soon! It will help you find schemes based on your profile.")
    
    with st.expander("Preview of upcoming questionnaire"):
        st.selectbox("Select your state", ["Maharashtra", "Delhi", "Karnataka"])
        st.radio("Social Category", ["General", "OBC", "SC", "ST"])
        st.radio("Are you a student?", ["Yes", "No"])
        st.radio("Are you differently abled?", ["Yes", "No"])
        st.radio("Do you belong to BPL category?", ["Yes", "No"])

def show_compare_schemes():
    # Back button in sidebar
    with st.sidebar:
        if st.button("← Back to Options"):
            st.session_state.current_page = "initial_options"
            st.rerun()
    
    st.title("Compare Schemes")
    
    # Placeholder UI for Compare Schemes
    st.info("This feature is coming soon! You'll be able to compare different schemes side by side.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Enter first scheme to compare")
    with col2:
        st.text_input("Enter second scheme to compare")
    
    st.button("Compare", disabled=True)

# Footer
st.markdown("---")
st.markdown("Powered by AI • Built for Indian Government Schemes")

# Main app logic
if st.session_state.current_page == "initial_options":
    show_initial_options()
elif st.session_state.current_page == "semantic_search":
    show_semantic_search()
elif st.session_state.current_page == "find_schemes":
    show_find_schemes()
elif st.session_state.current_page == "compare_schemes":
    show_compare_schemes() 