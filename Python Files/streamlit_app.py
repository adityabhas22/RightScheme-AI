import streamlit as st
from scheme_agent import process_query, create_scheme_agent, SchemeTools, extract_scheme_name
from typing import Dict, List
import json

# List of Indian states and UTs
INDIAN_STATES = [
    "Select State",
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

st.set_page_config(
    page_title="Government Schemes Assistant",
    page_icon="🏛️",
    layout="wide"
)

def initialize_session_state():
    if "scheme_agent" not in st.session_state:
        st.session_state.scheme_agent = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "user_state" not in st.session_state:
        st.session_state.user_state = None
    if "is_first_message" not in st.session_state:
        st.session_state.is_first_message = True
    if "current_scheme" not in st.session_state:
        st.session_state.current_scheme = None
    if "show_eligibility_checker" not in st.session_state:
        st.session_state.show_eligibility_checker = False

def create_eligibility_checker(scheme_name: str, tools_instance: SchemeTools):
    """Create an interactive eligibility checker for a scheme."""
    try:
        with st.spinner("Loading eligibility criteria..."):
            criteria = tools_instance.parse_eligibility_criteria(scheme_name)
        
        if not criteria:
            st.warning("No specific eligibility criteria found for this scheme. Please refer to the scheme details above.")
            return
        
        st.subheader(f"📋 Eligibility Checker for {scheme_name}")
        st.write("Please answer these questions to check your eligibility:")
        
        # Create a form for better UX
        with st.form(key=f"eligibility_form_{scheme_name}"):
            answers = {}
            
            # Group questions by criteria type
            criteria_groups = {}
            for criterion in criteria:
                criteria_type = criterion.get("criteria_type", "other")
                if criteria_type not in criteria_groups:
                    criteria_groups[criteria_type] = []
                criteria_groups[criteria_type].append(criterion)
            
            # Display questions by group
            for criteria_type, questions in criteria_groups.items():
                if criteria_type != "other":  # Show other questions last
                    st.markdown(f"**{criteria_type.title()} Criteria**")
                    for criterion in questions:
                        question = criterion["question"]
                        explanation = criterion.get("explanation", "")
                        
                        # Add icons based on criteria type
                        icons = {
                            "age": "👤",
                            "income": "💰",
                            "occupation": "💼",
                            "location": "📍",
                            "other": "📋"
                        }
                        icon = icons.get(criteria_type, "📋")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"{icon} {question}")
                            if explanation:
                                st.caption(explanation)
                        with col2:
                            answers[question] = st.radio(
                                "Select",
                                options=["Yes", "No"],
                                key=f"eligibility_{scheme_name}_{hash(question)}",
                                label_visibility="collapsed",
                                horizontal=True
                            ) == "Yes"
            
            # Show other questions last
            if "other" in criteria_groups:
                st.markdown("**Other Criteria**")
                for criterion in criteria_groups["other"]:
                    question = criterion["question"]
                    explanation = criterion.get("explanation", "")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📋 {question}")
                        if explanation:
                            st.caption(explanation)
                    with col2:
                        answers[question] = st.radio(
                            "Select",
                            options=["Yes", "No"],
                            key=f"eligibility_{scheme_name}_{hash(question)}",
                            label_visibility="collapsed",
                            horizontal=True
                        ) == "Yes"
            
            submit_button = st.form_submit_button("Check Eligibility")
        
        if submit_button:
            with st.spinner("Checking eligibility..."):
                result = tools_instance.check_eligibility(scheme_name, answers)
            
            if result["eligible"]:
                st.success("✅ " + result["message"])
                st.write("Next Steps:", result["next_steps"])
                
                # Add application button
                if st.button("Start Application Process"):
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": f"How do I apply for {scheme_name}?"
                    })
                    st.rerun()
            else:
                st.error("❌ " + result["message"])
                if "failed_criteria" in result:
                    st.write("Unmet criteria:")
                    for criterion in result["failed_criteria"]:
                        st.write(f"• {criterion}")
                    
                    st.info("💡 You may want to check other schemes that better match your eligibility.")
    
    except Exception as e:
        st.error(f"An error occurred while checking eligibility. Please try again later.")
        print(f"Eligibility checker error: {str(e)}")

def main():
    initialize_session_state()
    
    st.title("🏛️ Government Schemes Assistant")
    
    # State selection in sidebar
    with st.sidebar:
        st.header("Your Location")
        selected_state = st.selectbox(
            "Select your state",
            options=INDIAN_STATES,
            index=0,
            key="state_selector"
        )
        
        if selected_state != "Select State":
            st.session_state.user_state = selected_state
            st.success(f"Showing schemes available in {selected_state} and Central Schemes")
        
        # Add scheme selection in sidebar if a scheme is detected
        if hasattr(st.session_state, 'current_scheme') and st.session_state.current_scheme:
            st.header("Current Scheme")
            st.info(f"📋 {st.session_state.current_scheme}")
            
            # Add eligibility checker button in sidebar
            if st.button("Check Eligibility for This Scheme"):
                st.session_state.show_eligibility_checker = True
        
        if st.button("Clear Conversation"):
            st.session_state.chat_history = []
            st.session_state.scheme_agent = None
            st.session_state.is_first_message = True
            st.session_state.current_scheme = None
            st.session_state.show_eligibility_checker = False
            st.rerun()

    # Main chat interface
    if st.session_state.user_state is None:
        st.info("👆 Please select your state from the sidebar to get started!")
        st.stop()

    # Create two columns
    chat_col, checker_col = st.columns([2, 1])

    with chat_col:
        # Display welcome message for first-time users
        if st.session_state.is_first_message:
            welcome_message = (
                f"👋 Welcome! I'll help you find government schemes available in {st.session_state.user_state} "
                "and central schemes that you can benefit from.\n\n"
                "You can ask me about:\n"
                "• Available schemes in your state\n"
                "• Eligibility criteria\n"
                "• Application process\n"
                "• Required documents\n"
                "• Benefits and features"
            )
            st.chat_message("assistant").write(welcome_message)

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if query := st.chat_input("Type your question here..."):
            st.session_state.is_first_message = False
            
            # Add state context to the query
            contextualized_query = f"For someone in {st.session_state.user_state}: {query}"
            
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": query})

            # Get response
            with st.spinner("Thinking..."):
                response_data = process_query(contextualized_query)

            # Add assistant response to chat history
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response_data["response"]}
            )

            # Show conversation summary in sidebar
            with st.sidebar:
                with st.expander("Conversation Summary", expanded=False):
                    st.write(response_data["conversation_summary"])

            st.rerun()

    # Show eligibility checker in the right column if a scheme is selected
    with checker_col:
        if hasattr(st.session_state, 'current_scheme') and st.session_state.current_scheme:
            st.markdown("### Eligibility Checker")
            st.markdown(f"**Current Scheme:** {st.session_state.current_scheme}")
            create_eligibility_checker(
                st.session_state.current_scheme,
                SchemeTools("vectorDb")
            )

if __name__ == "__main__":
    main() 