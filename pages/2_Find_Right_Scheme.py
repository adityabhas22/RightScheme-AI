import streamlit as st
from utils.common import initialize_session_state, display_state_selector
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
            "text": "What is your age?",
            "type": "number",
            "validation": lambda x: 0 <= x <= 120
        },
        {
            "id": "gender",
            "text": "What is your gender?",
            "type": "select",
            "options": ["Male", "Female", "Other"]
        },
        {
            "id": "category",
            "text": "Which category do you belong to?",
            "type": "select",
            "options": ["General", "SC", "ST", "OBC"]
        },
        {
            "id": "annual_income",
            "text": "What is your annual household income (in INR)?",
            "type": "number",
            "validation": lambda x: x >= 0
        },
        {
            "id": "occupation",
            "text": "What is your primary occupation?",
            "type": "select",
            "options": ["Student", "Farmer", "Self-employed", "Salaried", "Unemployed", "Other"]
        }
    ]

def format_initial_query(responses, state):
    return (
        f"I am a {responses['age']} year old {responses['gender'].lower()} from {state}, "
        f"belonging to {responses['category']} category. "
        f"My annual household income is Rs. {responses['annual_income']} "
        f"and I am {responses['occupation'].lower()} by occupation. "
        f"Please suggest government schemes that I am eligible for, "
        f"considering my profile. List the most relevant schemes first, "
        f"including specific details about eligibility, benefits, and how to apply."
    )

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
            with st.spinner("Finding relevant schemes..."):
                initial_query = st.session_state.chat_history[-1]["content"]
                response_data = process_query(initial_query)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response_data["response"]}
                )
                st.session_state.is_first_message = False
                st.rerun()

        # Handle follow-up questions
        if query := st.chat_input("Ask follow-up questions about schemes..."):
            st.session_state.chat_history.append({"role": "user", "content": query})
            
            with st.spinner("Thinking..."):
                response_data = process_query(query)
                
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response_data["response"]}
            )
            
            st.rerun()

if __name__ == "__main__":
    main() 