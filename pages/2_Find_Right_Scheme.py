import streamlit as st
from typing import Dict, List
from utils.common import initialize_session_state, display_state_selector, translate_text
from Python_Files.scheme_agent import process_query, create_scheme_agent
from Python_Files.scheme_matcher import SchemeCategory, SchemeMatch, SchemeMatcher, UserProfile
from Python_Files.translation_utils import translate_text, translate_to_english
from utils.logging_utils import logger

st.set_page_config(
    page_title="Find Right Scheme - RightScheme AI",
    page_icon="🎯",
    layout="wide"
)

# Initialize all required session state variables at the start
if "find_schemes" not in st.session_state:
    st.session_state.find_schemes = {
        "chat_history": [],
        "scheme_agent": create_scheme_agent(),  # Initialize with the agent
        "is_first_message": True,
        "current_question": 0,
        "user_responses": {},
        "questionnaire_completed": False
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

def show_scheme_details(scheme: SchemeMatch):
    """Display detailed information about a scheme in a modal."""
    with st.expander(f"Details for {scheme.scheme_name}", expanded=True):
        st.markdown(f"""
        ### 📋 Scheme Details
        
        #### Benefits
        {chr(10).join([f"• {benefit}" for benefit in scheme.benefits])}
        
        #### Eligibility Status
        """)
        
        # Display eligibility criteria with checkmarks/crosses
        for criterion, matches in scheme.eligibility_match.items():
            icon = "✅" if matches else "❌"
            st.markdown(f"{icon} {criterion}")
        
        st.markdown("#### How to Apply")
        st.write(scheme.application_process)
        
        # Add relevance score visualization
        st.progress(scheme.relevance_score)
        st.caption(f"Match Score: {scheme.relevance_score:.0%}")

def get_questions() -> List[Dict]:
    """Return the list of questionnaire questions."""
    return [
        {
            "id": "age",
            "text": translate_text("What is your age?"),
            "type": "number",
            "validation": lambda x: 0 <= x <= 120
        },
        {
            "id": "gender",
            "text": translate_text("What is your gender?"),
            "type": "select",
            "options": [
                translate_text("Male"),
                translate_text("Female"),
                translate_text("Other")
            ]
        },
        {
            "id": "category",
            "text": translate_text("Which category do you belong to?"),
            "type": "select",
            "options": [
                translate_text("General"),
                translate_text("SC"),
                translate_text("ST"),
                translate_text("OBC")
            ]
        },
        {
            "id": "annual_income",
            "text": translate_text("What is your annual household income (in INR)?"),
            "type": "number",
            "validation": lambda x: x >= 0
        },
        {
            "id": "occupation",
            "text": translate_text("What is your primary occupation?"),
            "type": "select",
            "options": [
                translate_text(opt) for opt in [
                    "Student", "Farmer", "Self-employed",
                    "Salaried", "Unemployed", "Other"
                ]
            ]
        },
        {
            "id": "education_level",
            "text": translate_text("What is your highest education level?"),
            "type": "select",
            "options": [
                translate_text(opt) for opt in [
                    "Below 10th", "10th Pass", "12th Pass",
                    "Graduate", "Post Graduate", "Other"
                ]
            ]
        }
    ]

def format_initial_query(responses: Dict, state: str) -> str:
    """Format user responses into an initial query string."""
    return (
        f"I am a {responses['age']} year old {responses['gender'].lower()} from {state}, "
        f"belonging to {responses['category']} category. "
        f"My annual household income is Rs. {responses['annual_income']} "
        f"and I am {responses['occupation'].lower()} by occupation. "
        f"My education level is {responses.get('education_level', 'not specified')}. "
        f"Please suggest government schemes that I am eligible for."
    )

def create_user_profile(responses: Dict, state: str) -> UserProfile:
    """Create a UserProfile instance from questionnaire responses."""
    return UserProfile(
        age=int(responses['age']),
        gender=responses['gender'],
        category=responses['category'],
        annual_income=float(responses['annual_income']),
        occupation=responses['occupation'],
        state=state,
        education_level=responses.get('education_level'),
        marital_status=responses.get('marital_status'),
        specific_needs=responses.get('specific_needs', [])
    )

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

def display_scheme_results(grouped_schemes: Dict[SchemeCategory, Dict[str, List[SchemeMatch]]]):
    """Display matched schemes organized by category and priority."""
    for category, priority_groups in grouped_schemes.items():
        st.header(f"📑 {category.value}")
        
        for priority_level in ["Highly Recommended", "Potentially Eligible", "Limited Eligibility"]:
            schemes = priority_groups[priority_level]
            if schemes:
                with st.expander(f"{priority_level} ({len(schemes)} schemes)"):
                    for scheme in schemes:
                        with st.container():
                            # Scheme Name
                            st.markdown(f"""
                            <h2 style='color: #1f77b4;'>{scheme.scheme_name}</h2>
                            """, unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Overview section
                            st.markdown("### Overview")
                            st.write(scheme.application_process)
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Benefits section
                            st.markdown("### Benefits")
                            st.markdown("<br>", unsafe_allow_html=True)
                            for benefit in scheme.benefits:
                                st.markdown(f"• {benefit}")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Eligibility section
                            st.markdown("### Eligibility")
                            st.markdown("<br>", unsafe_allow_html=True)
                            for criterion, matches in scheme.eligibility_match.items():
                                if criterion != "reason":
                                    status = "✅" if matches else "❌"
                                    criterion_text = criterion.replace('_', ' ').title()
                                    st.markdown(f"• {status} {criterion_text}")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Simple divider
                            st.markdown("-----------------")
                            st.markdown("<br>", unsafe_allow_html=True)

def main():
    initialize_session_state()
    
    st.title(translate_text("🎯 Find Right Scheme"))
    st.write(translate_text("Answer a few questions to discover the perfect schemes for you."))
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    with st.sidebar:
        if st.button(translate_text("Start New Search")):
            # Only clear Find Schemes state
            st.session_state.find_schemes = {
                "chat_history": [],
                "scheme_agent": create_scheme_agent(),  # Initialize with the agent
                "is_first_message": True,
                "current_question": 0,
                "user_responses": {},
                "questionnaire_completed": False
            }
            st.rerun()
    
    # Rest of the code remains same but use st.session_state.find_schemes instead
    if not st.session_state.find_schemes["questionnaire_completed"]:
        questions = get_questions()
        
        if st.session_state.find_schemes["current_question"] < len(questions):
            current_q = questions[st.session_state.find_schemes["current_question"]]
            response = st.selectbox(current_q["text"], 
                                  options=current_q.get("options", []),
                                  key=f"input_{current_q['id']}") if current_q["type"] == "select" else \
                      st.number_input(current_q["text"], 
                                    min_value=0, 
                                    key=f"input_{current_q['id']}")
            
            col1, col2 = st.columns([1, 5])
            
            if col1.button("Next"):
                st.session_state.find_schemes["user_responses"][current_q["id"]] = response
                st.session_state.find_schemes["current_question"] += 1
                
                if st.session_state.find_schemes["current_question"] == len(questions):
                    st.session_state.find_schemes["questionnaire_completed"] = True
                    # Format and add initial query to chat history
                    initial_query = format_initial_query(
                        st.session_state.find_schemes["user_responses"],
                        st.session_state.user_state
                    )
                    st.session_state.find_schemes["chat_history"].append({"role": "user", "content": initial_query})
                st.rerun()
                
            if st.session_state.find_schemes["current_question"] > 0:
                if col1.button("Previous"):
                    st.session_state.find_schemes["current_question"] -= 1
                    st.rerun()
    
    # Process initial query or handle user input
    if st.session_state.find_schemes["questionnaire_completed"]:
        if st.session_state.find_schemes["is_first_message"]:
            display_thinking_animation()
            initial_query = st.session_state.find_schemes["chat_history"][-1]["content"]
            response_data = process_query(initial_query)

            # Log initial questionnaire response
            logger.log_conversation(
                conversation_type="find_schemes",
                user_query=initial_query,
                response=response_data["response"],
                metadata={
                    "state": st.session_state.user_state,
                    "language": st.session_state.language,
                    "user_profile": st.session_state.find_schemes["user_responses"],
                    "interaction_type": "initial_questionnaire"
                }
            )

            # Add to chat history
            st.session_state.find_schemes["chat_history"].append(
                {"role": "assistant", "content": response_data["response"]}
            )
            st.session_state.find_schemes["is_first_message"] = False
            st.rerun()

        # Handle follow-up questions
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