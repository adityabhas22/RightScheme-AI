import streamlit as st
from utils.common import initialize_session_state, display_state_selector, translate_text
from Python_Files.scheme_agent import process_query, create_scheme_agent

st.set_page_config(
    page_title="Find Right Scheme - RightScheme AI",
    page_icon="🎯",
    layout="wide"
)

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

def get_questions():
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
        }
    ]

def format_initial_query(responses, state):
    return (
        f"I am a {responses['age']} year old {responses['gender'].lower()} from {state}, "
        f"belonging to {responses['category']} category. "
        f"My annual household income is Rs. {responses['annual_income']} "
        f"and I am {responses['occupation'].lower()} by occupation. "
        f"Please suggest government schemes that I am eligible for, "
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

def main():
    initialize_session_state()
    initialize_questionnaire_state()
    
    st.title("🎯 Find Right Scheme")
    st.write("Answer a few questions to discover the perfect schemes for you.")
    
    # State selection in sidebar
    selected_state = display_state_selector()
    
    with st.sidebar:
        if st.button("Start New Search"):
            st.session_state.current_question = 0
            st.session_state.user_responses = {}
            st.session_state.questionnaire_completed = False
            st.session_state.chat_history = []
            st.session_state.is_first_message = True
            st.rerun()
    
    if st.session_state.user_state is None:
        st.info("👆 Please select your state from the sidebar to get started!")
        st.stop()

    # Display questionnaire if not completed
    if not st.session_state.questionnaire_completed:
        questions = get_questions()
        
        if st.session_state.current_question < len(questions):
            current_q = questions[st.session_state.current_question]
            response = st.selectbox(current_q["text"], 
                                  options=current_q.get("options", []),
                                  key=f"input_{current_q['id']}") if current_q["type"] == "select" else \
                      st.number_input(current_q["text"], 
                                    min_value=0, 
                                    key=f"input_{current_q['id']}")
            
            col1, col2 = st.columns([1, 5])
            
            if col1.button("Next"):
                st.session_state.user_responses[current_q["id"]] = response
                st.session_state.current_question += 1
                
                if st.session_state.current_question == len(questions):
                    st.session_state.questionnaire_completed = True
                    # Format and add initial query to chat history
                    initial_query = format_initial_query(
                        st.session_state.user_responses,
                        st.session_state.user_state
                    )
                    st.session_state.chat_history.append({"role": "user", "content": initial_query})
                st.rerun()
                
            if st.session_state.current_question > 0:
                if col1.button("Previous"):
                    st.session_state.current_question -= 1
                    st.rerun()
    
    # Display chat interface
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Process initial query or handle user input
    if st.session_state.questionnaire_completed:
        if st.session_state.is_first_message:
            display_thinking_animation()
            initial_query = st.session_state.chat_history[-1]["content"]
            response_data = process_query(initial_query)

            with st.chat_message("assistant"):
                st.write(response_data["response"])

            st.session_state.chat_history.append(
                {"role": "assistant", "content": response_data["response"]}
            )
            st.session_state.is_first_message = False
            st.rerun()

        # Handle follow-up questions
        if query := st.chat_input("Ask follow-up questions about schemes..."):
            # Immediately display user message
            with st.chat_message("user"):
                st.write(query)

            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": query})
            
            # Show thinking animation
            display_thinking_animation()
            
            # Add state context to the query
            contextualized_query = f"For someone in {st.session_state.user_state}: {query}"
            
            # Get response
            response_data = process_query(contextualized_query)
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response_data["response"])
            
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response_data["response"]}
            )

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