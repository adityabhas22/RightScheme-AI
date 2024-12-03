import streamlit as st
from utils.common import initialize_session_state, display_state_selector, translate_text

# Set page config
st.set_page_config(
    page_title="Compare & Choose - RightScheme AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add after the page config
st.markdown("""
    <style>
        /* Prevent link styling on hover */
        div[data-testid="stMarkdown"] div {
            pointer-events: none !important;
        }
        
        /* Only allow pointer events on actual buttons/links */
        a, .card-button, button {
            pointer-events: auto !important;
        }
        
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
        
        /* Main content styling */
        .main-content {
            background-color: #FFFFFF;
            border-radius: 1rem;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }
        
        /* Comparison card styling */
        .comparison-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        /* Table styling */
        .stTable {
            border: 1px solid #E2E8F0 !important;
            border-radius: 0.5rem !important;
            overflow: hidden !important;
        }
        
        .stTable th {
            background-color: #2C4875 !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            padding: 1rem !important;
        }
        
        .stTable td {
            color: #2D3748 !important;
            padding: 0.75rem 1rem !important;
        }
        
        .stTable tr:nth-child(even) {
            background-color: #F8FAFC !important;
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
            padding: 1rem !important;
        }
        
        /* Loading animation */
        .stSpinner > div {
            border-top-color: #5785D9 !important;
        }
        
        /* List styling */
        ul {
            color: #2D3748 !important;
            margin-left: 1.5rem !important;
        }
        
        li {
            margin-bottom: 0.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    initialize_session_state()
    
    st.markdown('<h1 style="color: #2C4875;">📊 Compare Schemes</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #2D3748; font-size: 1.1rem;">Compare different government schemes side by side to make informed decisions.</p>', unsafe_allow_html=True)
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    if st.session_state.user_state is None:
        st.markdown("""
            <div class="stAlert" style="background-color: #8FB8ED20; border: 1px solid #8FB8ED; padding: 1rem; border-radius: 0.5rem;">
                <p style="color: #2C4875; margin: 0;">👆 Please select your state from the sidebar to get started!</p>
            </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Placeholder content with better styling
    st.markdown("""
        <div class="comparison-card">
            <h3 style="color: #2C4875; margin-bottom: 1.5rem;">Coming Soon!</h3>
            <p style="color: #2D3748; margin-bottom: 1rem;">This section will allow you to:</p>
            <ul style="color: #2D3748; margin-bottom: 1.5rem;">
                <li>Compare multiple schemes side by side</li>
                <li>See detailed benefit comparisons</li>
                <li>Understand eligibility differences</li>
                <li>Make informed decisions about which schemes to apply for</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 