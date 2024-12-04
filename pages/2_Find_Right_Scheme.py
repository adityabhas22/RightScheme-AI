import streamlit as st
from typing import Dict, List, Any
from Python_Files.scheme_semantic_matcher import SemanticSchemeMatcher, UserProfile, SchemeRecommendation
from Python_Files.scheme_matcher import SchemeCategory, SchemeMatch
from utils.common import initialize_session_state, display_state_selector, translate_text, check_state_selection, get_greeting_message
from utils.logging_utils import logger
from Python_Files.scheme_agent import process_query, create_scheme_agent
from Python_Files.translation_utils import translate_to_english

st.set_page_config(
    page_title="Find Right Scheme - RightScheme AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
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
        
        /* Question card styling */
        .question-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(44, 72, 117, 0.1);
        }
        
        /* Radio button styling */
        .stRadio > div {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
            transition: all 0.2s ease;
        }
        
        .stRadio > div:hover {
            border-color: #5785D9;
            background-color: rgba(87, 133, 217, 0.05);
        }
        
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: #5785D9 !important;
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
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            /* Adjust question cards */
            .question-card {
                padding: 1rem;
                margin: 0.5rem 0;
            }
            
            /* Adjust input fields */
            .stTextInput input,
            .stSelectbox select,
            .stNumberInput input {
                font-size: 1rem !important;
            }
            
            /* Adjust buttons */
            .stButton button {
                width: 100% !important;
                padding: 0.5rem !important;
                margin: 0.25rem 0 !important;
            }
            
            /* Adjust scheme results */
            .scheme-container {
                padding: 0.75rem;
            }
            
            /* Adjust expandable sections */
            .streamlit-expanderHeader {
                font-size: 1rem !important;
            }
            
            /* Adjust scheme details */
            .scheme-details {
                padding: 0.5rem;
            }
            
            /* Optimize progress indicators */
            .stProgress {
                margin: 0.5rem 0 !important;
            }
            
            /* Adjust text sizes */
            .card-title {
                font-size: 1.2rem !important;
            }
            
            .card-description {
                font-size: 0.9rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Initialize all required session state variables at the start
if "find_schemes" not in st.session_state:
    st.session_state.find_schemes = {
        "chat_history": [],
        "scheme_agent": create_scheme_agent(),
        "scheme_matcher": SemanticSchemeMatcher(),
        "is_first_message": True,
        "current_question": 0,
        "user_responses": {},
        "questionnaire_completed": False,
        "recommendations": None
    }

def initialize_questionnaire_state():
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "user_responses" not in st.session_state:
        st.session_state.user_responses = {}
    if "questionnaire_completed" not in st.session_state:
        st.session_state.questionnaire_completed = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "scheme_agent" not in st.session_state:
        st.session_state.scheme_agent = None
    if "is_first_message" not in st.session_state:
        st.session_state.is_first_message = True

def show_scheme_details(scheme: SchemeRecommendation):
    """Display detailed information about a scheme in a modal."""
    with st.expander(f"Details for {scheme.scheme_name}", expanded=True):
        st.markdown(f"""
        ### 📋 Scheme Details
        
        #### Why Recommended
        {scheme.why_recommended}
        
        #### Benefits
        {chr(10).join([f"• {benefit}" for benefit in scheme.benefits])}
        
        #### Eligibility Status
        """)
        
        # Update to use eligibility_requirements and eligibility_status
        for criterion, requirement in scheme.eligibility_requirements.items():
            matches = scheme.eligibility_status.get(criterion, False)
            icon = "✅" if matches else "❌"
            st.markdown(f"{icon} **{criterion}**: {requirement}")
        
        st.markdown("#### How to Apply")
        for step in scheme.application_process:
            st.markdown(f"• {step}")
        
        # Add relevance score visualization
        st.progress(scheme.relevance_score)
        st.caption(f"Match Score: {scheme.relevance_score:.0%}")

def get_dynamic_questions(responses: Dict) -> List[Dict]:
    """Return dynamic questions based on previous responses."""
    base_questions = [
        {
            "id": "occupation_category",
            "text": translate_text("Which category best describes you?"),
            "type": "select",
            "options": [
                translate_text("Student"),
                translate_text("Employed"),
                translate_text("Self-employed/Business"),
                translate_text("Unemployed"),
                translate_text("Senior Citizen"),
                translate_text("Farmer/Agricultural Worker")
            ],
            "required": True,
            "category": "Basic Information"
        },
        {
            "id": "age",
            "text": translate_text("What is your age?"),
            "type": "number",
            "validation": lambda x: 0 <= x <= 120,
            "required": True,
            "category": "Basic Information"
        },
        {
            "id": "gender",
            "text": translate_text("What is your gender?"),
            "type": "select",
            "options": [
                translate_text("Male"),
                translate_text("Female"),
                translate_text("Other")
            ],
            "required": True,
            "category": "Basic Information"
        },
        {
            "id": "category",
            "text": translate_text("Which social category do you belong to?"),
            "type": "select",
            "options": [
                translate_text("General"),
                translate_text("SC"),
                translate_text("ST"),
                translate_text("OBC")
            ],
            "required": True,
            "category": "Basic Information"
        },
        {
            "id": "annual_income",
            "text": translate_text("What is your annual household income (in INR)?"),
            "type": "number",
            "validation": lambda x: x >= 0,
            "required": True,
            "category": "Financial Information"
        }
    ]

    # Add category-specific questions based on occupation_category
    if "occupation_category" in responses:
        if responses["occupation_category"] == "Student":
            base_questions.extend([
                {
                    "id": "education_level",
                    "text": translate_text("What is your current education level?"),
                    "type": "select",
                    "options": [
                        translate_text("School Student"),
                        translate_text("Undergraduate"),
                        translate_text("Postgraduate"),
                        translate_text("Research Scholar")
                    ],
                    "category": "Education Details"
                },
                {
                    "id": "institution_type",
                    "text": translate_text("What type of institution do you study in?"),
                    "type": "select",
                    "options": [
                        translate_text("Government"),
                        translate_text("Private"),
                        translate_text("Aided")
                    ],
                    "category": "Education Details"
                },
                {
                    "id": "specific_requirement",
                    "text": translate_text("What specific support are you looking for?"),
                    "type": "multiselect",
                    "options": [
                        translate_text("Education Loan"),
                        translate_text("Scholarship"),
                        translate_text("Skill Development"),
                        translate_text("Research Funding")
                    ],
                    "category": "Requirements"
                }
            ])

        elif responses["occupation_category"] == "Employed":
            base_questions.extend([
                {
                    "id": "employment_sector",
                    "text": translate_text("Which sector do you work in?"),
                    "type": "select",
                    "options": [
                        translate_text("Government"),
                        translate_text("Private"),
                        translate_text("Public Sector")
                    ],
                    "category": "Employment Details"
                },
                {
                    "id": "specific_requirement",
                    "text": translate_text("What specific support are you looking for?"),
                    "type": "multiselect",
                    "options": [
                        translate_text("Housing"),
                        translate_text("Skill Enhancement"),
                        translate_text("Business Loan"),
                        translate_text("Personal Loan")
                    ],
                    "category": "Requirements"
                }
            ])

        elif responses["occupation_category"] == "Self-employed/Business":
            base_questions.extend([
                {
                    "id": "business_type",
                    "text": translate_text("What is your business size?"),
                    "type": "select",
                    "options": [
                        translate_text("Micro"),
                        translate_text("Small"),
                        translate_text("Medium")
                    ],
                    "category": "Business Details"
                },
                {
                    "id": "annual_turnover",
                    "text": translate_text("What is your annual business turnover (in INR)?"),
                    "type": "number",
                    "validation": lambda x: x >= 0,
                    "category": "Business Details"
                },
                {
                    "id": "specific_requirement",
                    "text": translate_text("What specific support are you looking for?"),
                    "type": "multiselect",
                    "options": [
                        translate_text("Business Loan"),
                        translate_text("Equipment Purchase"),
                        translate_text("Working Capital"),
                        translate_text("Business Expansion")
                    ],
                    "category": "Requirements"
                }
            ])

        elif responses["occupation_category"] == "Unemployed":
            base_questions.extend([
                {
                    "id": "education_level",
                    "text": translate_text("What is your highest education level?"),
                    "type": "select",
                    "options": [
                        translate_text("Below 10th"),
                        translate_text("10th Pass"),
                        translate_text("12th Pass"),
                        translate_text("Graduate"),
                        translate_text("Post Graduate")
                    ],
                    "category": "Education Details"
                },
                {
                    "id": "specific_requirement",
                    "text": translate_text("What specific support are you looking for?"),
                    "type": "multiselect",
                    "options": [
                        translate_text("Skill Development"),
                        translate_text("Self-employment Schemes"),
                        translate_text("Job Training")
                    ],
                    "category": "Requirements"
                }
            ])

        elif responses["occupation_category"] == "Senior Citizen":
            base_questions.extend([
                {
                    "id": "living_status",
                    "text": translate_text("What is your living status?"),
                    "type": "select",
                    "options": [
                        translate_text("Living Alone"),
                        translate_text("Living with Family")
                    ],
                    "category": "Living Details"
                },
                {
                    "id": "specific_requirement",
                    "text": translate_text("What specific support are you looking for?"),
                    "type": "multiselect",
                    "options": [
                        translate_text("Pension Schemes"),
                        translate_text("Healthcare"),
                        translate_text("Financial Security")
                    ],
                    "category": "Requirements"
                }
            ])

        elif responses["occupation_category"] == "Farmer/Agricultural Worker":
            base_questions.extend([
                {
                    "id": "land_holding",
                    "text": translate_text("What is your land holding size (in acres)?"),
                    "type": "number",
                    "validation": lambda x: x >= 0,
                    "category": "Agricultural Details"
                },
                {
                    "id": "farming_type",
                    "text": translate_text("What type of farming do you practice?"),
                    "type": "select",
                    "options": [
                        translate_text("Traditional"),
                        translate_text("Organic"),
                        translate_text("Mixed")
                    ],
                    "category": "Agricultural Details"
                },
                {
                    "id": "specific_requirement",
                    "text": translate_text("What specific support are you looking for?"),
                    "type": "multiselect",
                    "options": [
                        translate_text("Crop Loans"),
                        translate_text("Equipment Purchase"),
                        translate_text("Irrigation Schemes"),
                        translate_text("Subsidies")
                    ],
                    "category": "Requirements"
                }
            ])

    # Add disability-related questions for all
    base_questions.append({
        "id": "disability_status",
        "text": translate_text("Do you have any disabilities?"),
        "type": "select",
        "options": [
            translate_text("No"),
            translate_text("Yes")
        ],
        "category": "Health Information"
    })

    # Add disability-specific questions if applicable
    if "disability_status" in responses and responses["disability_status"] == "Yes":
        base_questions.append({
            "id": "disability_type",
            "text": translate_text("What type of disability do you have?"),
            "type": "multiselect",
            "options": [
                translate_text("Physical"),
                translate_text("Visual"),
                translate_text("Hearing"),
                translate_text("Cognitive"),
                translate_text("Other")
            ],
            "category": "Health Information"
        })

    return base_questions

def display_questionnaire():
    """Display the dynamic questionnaire with progress bar."""
    questions = get_dynamic_questions(st.session_state.find_schemes["user_responses"])
    total_questions = len(questions)
    current_q_index = st.session_state.find_schemes["current_question"]
    
    # Display progress bar
    progress = (current_q_index) / total_questions
    st.progress(progress)
    st.markdown(f"Question {current_q_index + 1} of {total_questions}")
    
    if current_q_index < total_questions:
        current_q = questions[current_q_index]
        
        # Display category header if it's the first question of a category
        if current_q_index == 0 or questions[current_q_index - 1]["category"] != current_q["category"]:
            st.markdown(f"### {translate_text(current_q['category'])}")
        
        # Display the question in a card
        with st.container():
            st.markdown("""
                <div class="question-card">
            """, unsafe_allow_html=True)
            
            if current_q["type"] == "text":
                response = st.text_input(
                    current_q["text"],
                    placeholder=current_q.get("placeholder", ""),
                    key=f"input_{current_q['id']}"
                )
            elif current_q["type"] == "select":
                response = st.selectbox(
                    current_q["text"],
                    options=current_q["options"],
                    key=f"input_{current_q['id']}"
                )
            elif current_q["type"] == "multiselect":
                response = st.multiselect(
                    current_q["text"],
                    options=current_q["options"],
                    key=f"input_{current_q['id']}"
                )
            elif current_q["type"] == "number":
                response = st.number_input(
                    current_q["text"],
                    min_value=0,
                    key=f"input_{current_q['id']}"
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        
        if col1.button("Previous", key="prev_button", disabled=current_q_index == 0):
            st.session_state.find_schemes["current_question"] -= 1
            st.rerun()
            
        if col2.button("Next", key="next_button"):
            st.session_state.find_schemes["user_responses"][current_q["id"]] = response
            st.session_state.find_schemes["current_question"] += 1
            
            if current_q_index == total_questions - 1:
                st.session_state.find_schemes["questionnaire_completed"] = True
                if handle_questionnaire_completion(
                    st.session_state.find_schemes["user_responses"],
                    st.session_state.user_state
                ):
                    st.rerun()
            else:
                st.rerun()

def format_initial_query(responses: Dict, state: str) -> str:
    """Format user responses into an initial query string."""
    # Get specific requirements if available
    specific_reqs = responses.get('specific_requirement', [])
    specific_reqs_str = ", ".join(specific_reqs) if specific_reqs else "not specified"
    
    # Build occupation details string
    occupation_details = ""
    if responses.get('occupation_category') == "Student":
        occupation_details = f"studying in {responses.get('institution_type', 'not specified')} institution"
    elif responses.get('occupation_category') == "Employed":
        occupation_details = f"working in {responses.get('employment_sector', 'not specified')} sector"
    elif responses.get('occupation_category') == "Self-employed/Business":
        occupation_details = f"running a {responses.get('business_type', 'not specified')} business"
    elif responses.get('occupation_category') == "Farmer/Agricultural Worker":
        occupation_details = f"practicing {responses.get('farming_type', 'not specified')} farming"
    elif responses.get('occupation_category') == "Senior Citizen":
        occupation_details = f"{responses.get('living_status', 'not specified')}"
    
    # Build disability string if applicable
    disability_str = ""
    if responses.get('disability_status') == "Yes" and responses.get('disability_type'):
        disability_str = f" I have {', '.join(responses['disability_type'])} disability."
    
    return (
        f"I am a {responses['age']} year old {responses['gender'].lower()} from {state}, "
        f"belonging to {responses['category']} category. "
        f"My annual household income is Rs. {responses['annual_income']}. "
        f"I am a {responses['occupation_category']} {occupation_details}. "
        f"My specific requirements are: {specific_reqs_str}. "
        f"{disability_str} "
        f"Please suggest government schemes that I am eligible for, particularly related to my requirements."
    )

def create_user_profile(responses: Dict, state: str) -> UserProfile:
    """Create a UserProfile instance from questionnaire responses."""
    specific_needs = []
    
    # Add specific requirements to needs
    if responses.get('specific_requirement'):
        specific_needs.extend(responses['specific_requirement'])
    
    # Add disability information if present
    if responses.get('disability_status') == "Yes":
        specific_needs.extend(responses.get('disability_type', []))
    
    # Add occupation-specific details
    occupation_details = {}
    if responses['occupation_category'] == "Student":
        occupation_details = {
            'education_level': responses.get('education_level'),
            'institution_type': responses.get('institution_type'),
            'specific_requirements': responses.get('specific_requirement', [])
        }
    elif responses['occupation_category'] == "Employed":
        occupation_details = {
            'employment_sector': responses.get('employment_sector'),
            'specific_requirements': responses.get('specific_requirement', [])
        }
    elif responses['occupation_category'] == "Self-employed/Business":
        occupation_details = {
            'business_type': responses.get('business_type'),
            'annual_turnover': responses.get('annual_turnover'),
            'specific_requirements': responses.get('specific_requirement', [])
        }
    elif responses['occupation_category'] == "Farmer/Agricultural Worker":
        occupation_details = {
            'land_holding': responses.get('land_holding'),
            'farming_type': responses.get('farming_type'),
            'specific_requirements': responses.get('specific_requirement', [])
        }
    elif responses['occupation_category'] == "Senior Citizen":
        occupation_details = {
            'living_status': responses.get('living_status'),
            'specific_requirements': responses.get('specific_requirement', [])
        }
    elif responses['occupation_category'] == "Unemployed":
        occupation_details = {
            'education_level': responses.get('education_level'),
            'specific_requirements': responses.get('specific_requirement', [])
        }

    # Convert specific_needs list to string for interests
    interests_str = ", ".join(specific_needs) if specific_needs else ""

    # Only include marital status if provided in responses
    profile_args = {
        'age': int(responses['age']),
        'gender': responses['gender'],
        'category': responses['category'],
        'annual_income': float(responses['annual_income']),
        'occupation': responses['occupation_category'],
        'occupation_details': occupation_details,
        'state': state,
        'education_level': responses.get('education_level'),
        'specific_needs': specific_needs,
        'interests': interests_str,  # Now using the string version
    }
    
    # Add marital status only if provided
    if 'marital_status' in responses:
        profile_args['marital_status'] = responses['marital_status']

    return UserProfile(**profile_args)

def display_thinking_animation():
    """Display a simple thinking text with fade animation."""
    with st.chat_message("assistant"):
        st.markdown("""
            <div class="thinking-animation">Thinking...</div>
            <style>
                .thinking-animation {
                    animation: thinking 1.5s ease-in-out infinite;
                    color: #666;
                }
                @keyframes thinking {
                    0%, 100% { opacity: 0.3; }
                    50% { opacity: 1; }
                }
            </style>
        """, unsafe_allow_html=True)

def display_bilingual_message(message: str, role: str):
    """Display message in both English and selected language if not English."""
    with st.chat_message(role):
        # Always show English
        st.write(message)
        
        # Show translation if language is not English
        if st.session_state.language != "en":
            st.markdown("---")
            st.markdown(f"**{translate_text('Translation')}:**")
            st.write(translate_text(message))

def display_recommendations(recommendations: List[SchemeRecommendation]):
    """Display scheme recommendations in an organized manner."""
    st.markdown("### 🎯 Top Recommended Schemes")
    
    for i, scheme in enumerate(recommendations, 1):
        with st.expander(f"{i}. {scheme.scheme_name}", expanded=i==1):
            # Why recommended section
            st.markdown("#### 💡 Why This Scheme")
            st.write(scheme.why_recommended)
            
            # Benefits section
            st.markdown("#### 📋 Key Benefits")
            for benefit in scheme.benefits:
                st.markdown(f"• {benefit}")
            
            # Eligibility section with detailed criteria
            st.markdown("#### ✅ Eligibility Status")
            
            # Create two columns for better organization
            col1, col2 = st.columns(2)
            
            # Split eligibility criteria between columns
            criteria_items = list(scheme.eligibility_requirements.items())
            mid_point = len(criteria_items) // 2
            
            with col1:
                for criterion, requirement in list(criteria_items[:mid_point]):
                    matches = scheme.eligibility_status.get(criterion, False)
                    icon = "✅" if matches else "❌"
                    criterion_text = criterion.replace('_', ' ').title()
                    st.markdown(f"{icon} **{criterion_text}**")
                    st.markdown(f"   *Requirement: {requirement}*")
            
            with col2:
                for criterion, requirement in list(criteria_items[mid_point:]):
                    matches = scheme.eligibility_status.get(criterion, False)
                    icon = "✅" if matches else "❌"
                    criterion_text = criterion.replace('_', ' ').title()
                    st.markdown(f"{icon} **{criterion_text}**")
                    st.markdown(f"   *Requirement: {requirement}*")
            
            # Application process
            st.markdown("#### 📝 How to Apply")
            for step in scheme.application_process:
                st.markdown(f"• {step}")
            
            # Show relevance score
            st.progress(scheme.relevance_score)
            st.caption(f"Match Score: {scheme.relevance_score:.0%}")

def handle_questionnaire_completion(responses: Dict, state: str):
    """Handle the completion of the questionnaire."""
    try:
        with st.spinner("Finding the best schemes for you..."):
            # Create user profile
            user_profile = create_user_profile(responses, state)
            
            # Get scheme recommendations
            matcher = st.session_state.find_schemes["scheme_matcher"]
            recommendations = matcher.get_scheme_recommendations(user_profile)
            
            if not recommendations:
                st.warning("No matching schemes found. Please try adjusting your responses.")
                return False
            
            # Store recommendations in session state
            st.session_state.find_schemes["recommendations"] = recommendations
            
            # Format initial query for chat
            initial_query = format_initial_query(responses, state)
            st.session_state.find_schemes["chat_history"].append(
                {"role": "user", "content": initial_query}
            )
            
            # Log the interaction
            logger.log_conversation(
                conversation_type="find_schemes",
                user_query=initial_query,
                response="Recommendations generated",
                metadata={
                    "state": state,
                    "language": st.session_state.language,
                    "user_profile": responses,
                    "interaction_type": "initial_questionnaire",
                    "num_recommendations": len(recommendations)
                }
            )
            
            return True
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.log_error("find_schemes", str(e), {"state": state})
        return False

def main():
    # Set current page for unique widget keys
    st.session_state['current_page'] = 'find_schemes'
    
    initialize_session_state()
    display_state_selector()
    
    # Add reset button to sidebar
    with st.sidebar:
        if st.button(translate_text("Start New Search")):
            # Only clear Find Schemes state
            st.session_state.find_schemes = {
                "chat_history": [],
                "scheme_agent": create_scheme_agent(),
                "scheme_matcher": SemanticSchemeMatcher(),
                "is_first_message": True,
                "current_question": 0,
                "user_responses": {},
                "questionnaire_completed": False,
                "recommendations": None
            }
            st.rerun()
    
    # Title and description first
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; pointer-events: none;">
            <div style="pointer-events: none;">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2C4875" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <circle cx="12" cy="12" r="6"></circle>
                    <circle cx="12" cy="12" r="2"></circle>
                </svg>
            </div>
            <h1 style="margin: 0; color: #2C4875; line-height: 32px;">""" + translate_text("Find Right Scheme") + """</h1>
        </div>
    """, unsafe_allow_html=True)
    st.write(translate_text("Answer a few questions to discover the perfect schemes for you."))
    
    # Check state selection before proceeding
    if not check_state_selection():
        return
        
    # Rest of the questionnaire code...
    if not st.session_state.find_schemes["questionnaire_completed"]:
        display_questionnaire()
    
    # Process recommendations and handle chat
    if st.session_state.find_schemes["questionnaire_completed"]:
        # Display recommendations if available
        if st.session_state.find_schemes["recommendations"]:
            display_recommendations(st.session_state.find_schemes["recommendations"])
            
            # Add a separator
            st.markdown("---")
            st.markdown("### 💬 Ask Follow-up Questions")
            st.markdown("Feel free to ask specific questions about any scheme or explore more options.")
        
        # Handle chat interface
        if query := st.chat_input(translate_text("Ask follow-up questions about schemes...")):
            # Translate query to English if in another language
            english_query = translate_to_english(query) if st.session_state.language != "en" else query
            
            # Add to chat history
            st.session_state.find_schemes["chat_history"].append({"role": "user", "content": query})
            
            # Show thinking animation
            display_thinking_animation()
            
            # Add state context to the query
            contextualized_query = f"For someone in {st.session_state.user_state}: {english_query}"
            
            # Get response
            response_data = process_query(contextualized_query)
            
            # Log follow-up conversation
            logger.log_conversation(
                conversation_type="find_schemes",
                user_query=query,
                response=response_data["response"],
                metadata={
                    "state": st.session_state.user_state,
                    "language": st.session_state.language,
                    "user_profile": st.session_state.find_schemes["user_responses"],
                    "interaction_type": "follow_up",
                    "english_query": english_query,
                    "contextualized_query": contextualized_query
                }
            )
            
            # Add to chat history
            st.session_state.find_schemes["chat_history"].append(
                {"role": "assistant", "content": response_data["response"]}
            )

    # Display chat history ONCE with translations
    for message in st.session_state.find_schemes["chat_history"]:
        display_bilingual_message(message["content"], message["role"])

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