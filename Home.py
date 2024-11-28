import streamlit as st

st.set_page_config(
    page_title="RightScheme AI",
    page_icon="🏛️",
    layout="wide"
)

def main():
    st.title("🏛️ Welcome to RightScheme AI")
    
    st.markdown("""
    ### Your Intelligent Guide to Government Schemes
    
    RightScheme AI helps citizens discover, understand, and access government welfare schemes 
    that are most relevant to them. Our platform combines advanced AI technology with 
    comprehensive scheme data to provide you with accurate, up-to-date information.
    
    ### Choose a Service:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 🔍 Semantic Search")
        st.write("Ask questions about any government scheme and get detailed answers.")
        if st.button("Go to Semantic Search", use_container_width=True):
            st.switch_page("pages/1_Semantic_Search.py")
    
    with col2:
        st.info("### 🎯 Find Right Scheme")
        st.write("Answer a few questions to discover schemes perfect for you.")
        if st.button("Go to Find Right Scheme", use_container_width=True):
            st.switch_page("pages/2_Find_Right_Scheme.py")
    
    with col3:
        st.info("### 📊 Compare Schemes")
        st.write("Compare different schemes side by side to make informed decisions.")
        if st.button("Go to Compare Schemes", use_container_width=True):
            st.switch_page("pages/3_Compare_Schemes.py")

    # Add responsive design CSS
    st.markdown("""
    <style>
        /* General mobile optimizations */
        @media (max-width: 768px) {
            .stMarkdown {
                padding: 0.5rem !important;
            }
            
            /* Adjust any chat containers */
            .element-container {
                margin: 0 !important;
                padding: 0 !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 