from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import streamlit as st
from utils.common import initialize_session_state
from Python_Files.translation_utils import translate_text

class QuestionType(Enum):
    SELECT = "select"
    NUMBER = "number"
    TEXT = "text"
    MULTISELECT = "multiselect"

@dataclass
class ValidationRule:
    condition: Callable[[Any], bool]
    error_message: str

class QuestionNode:
    def __init__(
        self,
        question_id: str,
        question_text: str,
        question_type: QuestionType,
        options: Optional[List[str]] = None,
        validation_rules: Optional[List[ValidationRule]] = None,
        follow_up_logic: Optional[Dict[str, str]] = None,
        required: bool = True
    ):
        self.question_id = question_id
        self.question_text = question_text
        self.question_type = question_type
        self.options = options or []
        self.validation_rules = validation_rules or []
        self.follow_up_logic = follow_up_logic or {}
        self.required = required
        
    def get_translated_text(self, language: str) -> str:
        """Get question text in specified language."""
        if language == "en":
            return self.question_text
        return translate_text(self.question_text, target_lang=language)
    
    def get_translated_options(self, language: str) -> List[str]:
        """Get options in specified language."""
        if language == "en":
            return self.options
        return [translate_text(option, target_lang=language) for option in self.options]
    
    def validate_response(self, response: Any) -> tuple[bool, Optional[str]]:
        """Validate user response against rules."""
        if self.required and (response is None or response == ""):
            return False, translate_text("This field is required")
        
        # For text type, any non-empty string is valid if required,
        # or any string (including empty) if not required
        if self.question_type == QuestionType.TEXT:
            return True, None
            
        for rule in self.validation_rules:
            try:
                if not rule.condition(response):
                    return False, translate_text(rule.error_message)
            except Exception as e:
                return False, translate_text("Invalid input")
                
        return True, None
    
    def get_next_question(self, response: Any) -> Optional[str]:
        """Determine next question based on response."""
        if self.question_type == QuestionType.SELECT and response in self.follow_up_logic:
            return self.follow_up_logic[response]
        elif self.question_type == QuestionType.NUMBER:
            # Handle numeric range based logic
            for range_str, next_q in self.follow_up_logic.items():
                try:
                    min_val, max_val = map(float, range_str.split('-'))
                    if min_val <= float(response) <= max_val:
                        return next_q
                except ValueError:
                    continue
        return self.follow_up_logic.get('default')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "options": self.options,
            "required": self.required,
            "follow_up_logic": self.follow_up_logic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionNode':
        """Create node from dictionary."""
        return cls(
            question_id=data["question_id"],
            question_text=data["question_text"],
            question_type=QuestionType(data["question_type"]),
            options=data.get("options", []),
            required=data.get("required", True),
            follow_up_logic=data.get("follow_up_logic", {})
        ) 

class AdaptiveQuestionnaire:
    def __init__(self, initial_question_id: str):
        """Initialize questionnaire with starting question ID."""
        self.questions: Dict[str, QuestionNode] = {}
        self.initial_question_id = initial_question_id
        
        # Initialize session state if needed
        if "adaptive_questionnaire" not in st.session_state:
            self.reset()
    
    def reset(self):
        """Reset questionnaire state."""
        st.session_state.adaptive_questionnaire = {
            "current_question_id": self.initial_question_id,
            "responses": {},
            "completed": False,
            "profile_built": False
        }
    
    def add_question(self, question: QuestionNode):
        """Add a question to the questionnaire."""
        self.questions[question.question_id] = question
        
    def get_current_question(self) -> Optional[QuestionNode]:
        """Get current question with translations."""
        current_id = st.session_state.adaptive_questionnaire["current_question_id"]
        return self.questions.get(current_id)
    
    def process_response(self, response: Any) -> tuple[bool, Optional[str]]:
        """Process user response and determine next question."""
        current_question = self.get_current_question()
        if not current_question:
            return False, "No current question found"
            
        # Validate response
        is_valid, error_msg = current_question.validate_response(response)
        if not is_valid:
            return False, error_msg
            
        # Store response
        st.session_state.adaptive_questionnaire["responses"][current_question.question_id] = response
        
        # Determine next question
        next_question_id = current_question.get_next_question(response)
        
        if next_question_id:
            st.session_state.adaptive_questionnaire["current_question_id"] = next_question_id
            return True, None
        else:
            # No more questions, mark as completed
            st.session_state.adaptive_questionnaire["completed"] = True
            return True, None
    
    def build_user_profile(self) -> Dict[str, Any]:
        """Convert questionnaire responses to structured user profile."""
        if not st.session_state.adaptive_questionnaire["completed"]:
            raise ValueError("Questionnaire not completed")
            
        responses = st.session_state.adaptive_questionnaire["responses"]
        
        # Map occupation types to standardized values
        occupation_mapping = {
            "Farmer": "Farmer",
            "Self-employed": "Self-employed",
            "Salaried": "Salaried",
            "Unemployed": "Unemployed",
            "Student": "Student",
            "Homemaker": "Homemaker",
            "Retired": "Retired"
        }
        
        # Map education levels to standardized values
        education_mapping = {
            "Below 10th": "Below 10th",
            "10th Pass": "10th Pass",
            "12th Pass": "12th Pass",
            "Graduate": "Graduate",
            "Post Graduate": "Post Graduate",
            "Other": "Other"
        }
        
        # Build basic profile
        profile = {
            "age": int(float(responses.get("basic_age", 0))),
            "gender": responses.get("basic_gender", ""),
            "category": responses.get("basic_category", ""),
            "occupation": occupation_mapping.get(responses.get("occupation_type", ""), ""),
            "education_level": education_mapping.get(responses.get("education_current_level", ""), ""),
            "annual_income": float(responses.get("financial_annual_income", 0)) if "financial_annual_income" in responses else float(responses.get("financial_family_income", 0)),
            "specific_needs": responses.get("needs_general", []),
            "additional_info": responses.get("open_search", "")
        }
        
        st.session_state.adaptive_questionnaire["profile_built"] = True
        return profile
    
    def get_progress(self) -> float:
        """Calculate questionnaire progress."""
        total_responses = len(st.session_state.adaptive_questionnaire["responses"])
        # Estimate progress based on typical path length
        estimated_total = len(self.questions) * 0.7  # Assume ~70% of questions are asked
        return min(1.0, total_responses / estimated_total)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize questionnaire structure."""
        return {
            "initial_question_id": self.initial_question_id,
            "questions": {
                qid: question.to_dict() 
                for qid, question in self.questions.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptiveQuestionnaire':
        """Create questionnaire from serialized data."""
        questionnaire = cls(data["initial_question_id"])
        for qid, q_data in data["questions"].items():
            questionnaire.add_question(QuestionNode.from_dict(q_data))
        return questionnaire

def create_default_questionnaire() -> AdaptiveQuestionnaire:
    """Create the default questionnaire with all questions and logic."""
    questionnaire = AdaptiveQuestionnaire("basic_age")
    
    # Basic Information Questions
    age_question = QuestionNode(
        question_id="basic_age",
        question_text="What is your age?",
        question_type=QuestionType.NUMBER,
        validation_rules=[
            ValidationRule(
                lambda x: 0 <= float(x) <= 120,
                "Please enter a valid age between 0 and 120"
            )
        ],
        follow_up_logic={
            "0-18": "basic_education_status",
            "19-60": "basic_gender",
            "61-120": "basic_gender",
            "default": "basic_gender"  # Add default path
        }
    )
    questionnaire.add_question(age_question)
    
    gender_question = QuestionNode(
        question_id="basic_gender",
        question_text="What is your gender?",
        question_type=QuestionType.SELECT,
        options=["Male", "Female", "Other"],
        follow_up_logic={
            "default": "basic_category"
        }
    )
    questionnaire.add_question(gender_question)
    
    category_question = QuestionNode(
        question_id="basic_category",
        question_text="Which category do you belong to?",
        question_type=QuestionType.SELECT,
        options=["General", "SC", "ST", "OBC", "Minority"],
        follow_up_logic={
            "default": "occupation_type"  # Changed to go directly to occupation
        }
    )
    questionnaire.add_question(category_question)
    
    # Occupation Questions
    occupation_type = QuestionNode(
        question_id="occupation_type",
        question_text="What is your primary occupation?",
        question_type=QuestionType.SELECT,
        options=["Farmer", "Self-employed", "Salaried", "Unemployed", "Student", "Homemaker", "Retired"],
        follow_up_logic={
            "Farmer": "financial_annual_income",
            "Self-employed": "financial_annual_income",
            "Salaried": "financial_annual_income",
            "Unemployed": "financial_family_income",
            "Student": "education_current_level",
            "Homemaker": "financial_family_income",
            "Retired": "financial_pension",
            "default": "financial_annual_income"
        }
    )
    questionnaire.add_question(occupation_type)
    
    # Education level questions
    education_current_level = QuestionNode(
        question_id="education_current_level",
        question_text="What is your current education level?",
        question_type=QuestionType.SELECT,
        options=["Below 10th", "10th Pass", "12th Pass", "Graduate", "Post Graduate", "Other"],
        follow_up_logic={
            "default": "financial_family_income"
        }
    )
    questionnaire.add_question(education_current_level)
    
    # Financial Questions
    annual_income = QuestionNode(
        question_id="financial_annual_income",
        question_text="What is your annual income (in INR)?",
        question_type=QuestionType.NUMBER,
        validation_rules=[
            ValidationRule(
                lambda x: float(x) >= 0,
                "Please enter a valid income amount"
            )
        ],
        follow_up_logic={
            "default": "needs_general"
        }
    )
    questionnaire.add_question(annual_income)
    
    family_income = QuestionNode(
        question_id="financial_family_income",
        question_text="What is your family's annual income (in INR)?",
        question_type=QuestionType.NUMBER,
        validation_rules=[
            ValidationRule(
                lambda x: float(x) >= 0,
                "Please enter a valid income amount"
            )
        ],
        follow_up_logic={
            "default": "needs_general"
        }
    )
    questionnaire.add_question(family_income)
    
    pension_income = QuestionNode(
        question_id="financial_pension",
        question_text="What is your monthly pension amount (in INR)?",
        question_type=QuestionType.NUMBER,
        validation_rules=[
            ValidationRule(
                lambda x: float(x) >= 0,
                "Please enter a valid amount"
            )
        ],
        follow_up_logic={
            "default": "needs_general"
        }
    )
    questionnaire.add_question(pension_income)
    
    # Needs Assessment
    needs_assessment = QuestionNode(
        question_id="needs_general",
        question_text="What type of government assistance are you primarily looking for?",
        question_type=QuestionType.MULTISELECT,
        options=[
            "Financial Support",
            "Education Support",
            "Healthcare Support",
            "Housing Support",
            "Business Support",
            "Agricultural Support",
            "Skill Development",
            "Other"
        ],
        follow_up_logic={
            "default": "open_search"
        }
    )
    questionnaire.add_question(needs_assessment)
    
    # Open-ended search question
    open_search = QuestionNode(
        question_id="open_search",
        question_text="Is there any specific scheme or support you're looking for? Feel free to describe in your own words:",
        question_type=QuestionType.TEXT,
        required=False,
        follow_up_logic={
            "default": None  # End of questionnaire
        }
    )
    questionnaire.add_question(open_search)
    
    return questionnaire