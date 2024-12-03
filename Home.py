import streamlit as st
from PIL import Image
import base64
from utils.common import initialize_session_state, display_state_selector, translate_text

def main():
    st.set_page_config(
        page_title="RightScheme AI",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="collapsed"
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

    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
        /* Main heading styles */
        .main-heading {
            color: #2C4875;
            font-size: 3.5rem !important;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        /* Subheading styles */
        .subheading {
            color: #2D3748;
            font-size: 1.5rem !important;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Card container */
        .card-container {
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(87, 133, 217, 0.1);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin: 1rem;
            height: 380px;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            overflow: hidden;
        }

        .card-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(87, 133, 217, 0.1), 0 10px 10px -5px rgba(87, 133, 217, 0.04);
            border-color: rgba(87, 133, 217, 0.2);
        }

        /* Card content */
        .card-content {
            text-align: center;
            flex-grow: 1;
            margin-bottom: 20px;
            width: 100%;
        }

        /* Card icon */
        .card-icon {
            width: 48px;
            height: 48px;
            margin: 0 auto 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .card-icon svg {
            width: 100%;
            height: 100%;
            stroke: #2C4875;
        }

        .card-title {
            color: #2C4875;
            font-size: 1.8rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .card-description {
            color: #2D3748;
            font-size: 1rem;
            line-height: 1.5;
            padding: 0 10px;
        }

        /* Button styles */
        .card-button {
            background-color: #2C4875;
            color: #FFFFFF !important;
            text-decoration: none;
            padding: 12px 0;
            border-radius: 8px;
            width: calc(100% - 40px);
            display: block;
            text-align: center;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            margin: 0 auto;
            position: absolute;
            bottom: 20px;
            left: 20px;
        }

        .card-button:hover {
            background-color: #5785D9;
            color: #FFFFFF !important;
            text-decoration: none;
        }

        /* Hide Streamlit elements */
        .stButton, .stDownloadButton, footer {
            display: none !important;
        }
        
        /* Selectbox styles */
        .stSelectbox {
            margin-bottom: 2rem;
        }
        
        /* Center align all content */
        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Hero section styles */
        .hero-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 2rem 1rem;
            margin-bottom: 2rem;
        }

        .title-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .title-icon {
            width: 3.5rem;
            height: 3.5rem;
            stroke: #2C4875;
        }

        .gradient-text {
            background: linear-gradient(90deg, #2C4875 0%, #5785D9 50%, #8FB8ED 100%);
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            font-size: 2.25rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
        }

        .mission-container {
            max-width: 800px;
            margin: 0 auto;
        }

        .mission-text {
            font-size: 1.125rem !important;
            color: #2D3748 !important;
            line-height: 1.7 !important;
            margin-bottom: 1rem !important;
        }

        .highlight {
            color: #5785D9 !important;
            font-weight: 600 !important;
        }

        .state-prompt {
            font-size: 0.875rem !important;
            color: #2D3748 !important;
            font-style: italic !important;
            margin: 1rem 0 !important;
        }

        /* Custom selectbox styling */
        .stSelectbox > div > div {
            background-color: white;
            border-radius: 0.5rem;
            border: 1px solid #E2E8F0;
        }
        
        /* Container styles */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }
        
        /* Flag icon */
        .flag-icon {
            width: 56px;
            height: 56px;
            margin: 0 auto 1rem auto;
            display: block;
        }
        
        /* Main title */
        h1.main-title {
            font-family: sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin: 1rem 0;
            color: #2C4875;
        }
        
        /* Mission text */
        .mission-text {
            font-size: 1.125rem;
            line-height: 1.7;
            text-align: center;
            color: #2D3748;
            margin: 1.5rem auto;
            max-width: 800px;
        }
        
        /* Highlight text */
        .highlight {
            color: #5785D9;
            font-weight: 600;
        }
        
        /* State prompt */
        .state-prompt {
            font-size: 0.875rem;
            color: #2D3748;
            text-align: center;
            font-style: italic;
            margin: 1rem 0;
        }
        
        /* Selectbox container */
        .select-container {
            max-width: 400px;
            margin: 0 auto;
        }
        
        /* Custom styling for select box */
        .stSelectbox > div > div {
            background-color: white;
            border: 1px solid #E2E8F0;
            border-radius: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Hero Section HTML
    st.markdown("""
    <div class="container">
        <svg class="flag-icon" viewBox="0 0 24 24" fill="none" stroke="#2C4875" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
            <line x1="4" y1="22" x2="4" y2="15"></line>
        </svg>
        <h1 class="main-title">RightScheme AI</h1>
        <div class="mission-text">
            Empowering citizens with <span class="highlight">intelligent access</span> to government welfare schemes.<br>
            We're bridging the gap between people and policies, making welfare schemes 
            <span class="highlight">accessible to everyone</span>.
        </div>
        <p class="state-prompt">
            Select your state to discover schemes available in your region
        </p>
    </div>
    """, unsafe_allow_html=True)

    # State Selection
    states = [
        "Select your state",
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
    ]

    # Center the select box
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected_state = st.selectbox("", states, index=0, key="state_selector")

    # Add spacing after the selectbox
    st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)

    # Feature Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card-container">
            <div class="card-content">
                <div class="card-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                </div>
                <h2 class="card-title">Smart Search</h2>
                <p class="card-description">Ask anything about government schemes and get instant, accurate answers</p>
            </div>
            <a href="/Semantic_Search" target="_self" class="card-button">Start Searching</a>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card-container">
            <div class="card-content">
                <div class="card-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <circle cx="12" cy="12" r="6"></circle>
                        <circle cx="12" cy="12" r="2"></circle>
                    </svg>
                </div>
                <h2 class="card-title">Perfect Match</h2>
                <p class="card-description">Find schemes tailored to your needs with our smart questionnaire</p>
            </div>
            <a href="/Find_Right_Scheme" target="_self" class="card-button">Find Schemes</a>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card-container">
            <div class="card-content">
                <div class="card-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 3v18h18"></path>
                        <path d="M18 17V9"></path>
                        <path d="M13 17V5"></path>
                        <path d="M8 17v-3"></path>
                    </svg>
                </div>
                <h2 class="card-title">Compare & Choose</h2>
                <p class="card-description">Compare schemes side by side to make the best choice for you</p>
            </div>
            <a href="/Compare_Schemes" target="_self" class="card-button">Compare Now</a>
        </div>
        """, unsafe_allow_html=True)

    # Add JavaScript for smooth navigation
    st.markdown("""
    <script>
        const buttons = document.querySelectorAll('.card-button');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const path = button.getAttribute('href');
                window.location.href = window.location.origin + path;
            });
        });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()