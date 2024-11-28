import streamlit as st
from query_vectordb import VectorDBQuerier
import os

# Initialize the VectorDBQuerier (do this once)
@st.cache_resource
def init_querier():
    vector_db_dir = "/Users/adityabhaskara/Coding Projects/Jupyter Labs/Experimenting/vectorDb"
    return VectorDBQuerier(vector_db_dir)

def main():
    st.set_page_config(
        page_title="Document Query System",
        page_icon="🔍",
        layout="wide"
    )

    # Initialize the querier
    querier = init_querier()

    st.title("📚 Government Schemes Query System")
    st.markdown("---")

    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # Main query input
        query = st.text_area(
            "Enter your query about government schemes:",
            height=100,
            placeholder="Example: What are the eligibility criteria for PM Kisan Scheme?"
        )

        # Query parameters
        col_params1, col_params2 = st.columns(2)
        
        with col_params1:
            k_results = st.slider(
                "Number of results to return",
                min_value=1,
                max_value=10,
                value=3
            )

        # Submit button
        if st.button("🔍 Search", type="primary"):
            if query:
                try:
                    with st.spinner("Searching..."):
                        # Search the vector database
                        results = querier.search(query, top_k=k_results)
                        
                        if results:
                            # Process results with LLM
                            response_data = querier.process_with_llm(query, results)
                            
                            # Display AI Response
                            st.markdown("### 🤖 AI Response")
                            st.write(response_data["ai_response"])
                            
                            # Display Sources
                            st.markdown("### 📚 Sources Used")
                            for i, source in enumerate(response_data["sources"], 1):
                                with st.expander(f"Source {i} - Relevance: {source['relevance']:.4f}"):
                                    st.markdown(f"**File:** {source['file']}")
                                    st.markdown(f"**Preview:** {source['text']}")
                            
                            # Display conversation history
                            with st.expander("Conversation History"):
                                st.write(response_data["chat_history"])
                        else:
                            st.warning("No relevant information found for your query.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter a query first.")

    with col2:
        st.markdown("### How to use")
        st.markdown("""
        1. Enter your query about government schemes in the text area
        2. Adjust the number of results you want to see
        3. Click the Search button
        
        **Tips:**
        - Be specific in your queries
        - Ask about specific schemes, eligibility criteria, or benefits
        - The system maintains conversation history for context
        - Check the sources used for additional information
        """)

if __name__ == "__main__":
    main() 