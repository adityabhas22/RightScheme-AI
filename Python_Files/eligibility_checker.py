from typing import List, Dict, Tuple
from scheme_agent import SchemeTools
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

class EligibilityQuestion:
    def __init__(self, question: str, criterion: str, is_actionable: bool = True):
        self.question = question
        self.criterion = criterion
        self.is_actionable = is_actionable
        self.answer = None
        self.category = self._categorize_criterion()

    def _categorize_criterion(self) -> str:
        """Categorize the criterion to determine appropriate actions."""
        criterion_lower = self.criterion.lower()
        
        categories = {
            'documentation': ['document', 'certificate', 'proof', 'aadhaar', 'id', 'pan'],
            'registration': ['register', 'enrollment', 'apply', 'application'],
            'financial': ['income', 'salary', 'earnings', 'bank', 'account'],
            'demographic': ['age', 'gender', 'caste', 'category', 'residence'],
            'property': ['land', 'house', 'property', 'asset'],
            'occupation': ['farmer', 'worker', 'business', 'employment', 'job'],
            'education': ['education', 'degree', 'qualification', 'study'],
            'family': ['family', 'household', 'dependent', 'married']
        }
        
        for category, keywords in categories.items():
            if any(keyword in criterion_lower for keyword in keywords):
                return category
        
        return 'other'

    def get_action_steps(self) -> List[str]:
        """Get relevant action steps based on the criterion category."""
        actions = {
            'documentation': [
                "Visit your nearest government office to obtain required documents",
                "Ensure all your documents are valid and not expired",
                "Get documents attested if required"
            ],
            'registration': [
                "Visit your nearest Common Service Centre (CSC)",
                "Check the official website for online registration",
                "Keep all required documents ready before registration"
            ],
            'financial': [
                "Open a bank account if you don't have one",
                "Ensure your bank account is linked to Aadhaar",
                "Maintain required minimum balance if specified"
            ],
            'demographic': [
                "Obtain/Update your category certificate if applicable",
                "Ensure your demographic details are correctly recorded in official documents"
            ],
            'property': [
                "Verify your property records at local revenue office",
                "Ensure property documents are in your name",
                "Update land records if needed"
            ],
            'occupation': [
                "Get your occupation certificate from relevant authority",
                "Register with relevant professional body if required",
                "Update employment records if needed"
            ],
            'education': [
                "Obtain required educational certificates",
                "Get certificates verified from issuing authorities",
                "Complete any mandatory educational requirements"
            ],
            'family': [
                "Update family records in relevant documents",
                "Obtain family income certificate if required",
                "Update ration card or family registry"
            ],
            'other': [
                "Contact local government office for guidance",
                "Seek assistance from scheme implementation authority"
            ]
        }
        
        return actions.get(self.category, actions['other'])

class EligibilityChecker:
    def __init__(self):
        self.scheme_tools = SchemeTools()
        self.llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")

    def get_scheme_criteria(self, scheme_name: str) -> str:
        """Get eligibility criteria with better error handling and fuzzy matching."""
        try:
            # First try direct search
            criteria = self.scheme_tools.get_eligibility_criteria(scheme_name)
            
            if criteria == "No eligibility criteria found for this scheme.":
                # Try searching with variations of the scheme name
                search_results = self.scheme_tools.search_scheme(scheme_name)
                
                if search_results:
                    # Print found schemes for verification
                    print("\nFound similar schemes:")
                    for i, scheme in enumerate(search_results[:5], 1):
                        print(f"{i}. {scheme.scheme_name} (Relevance: {scheme.relevance_score:.2f})")
                        if scheme.relevance_score > 0.8:  # High confidence match
                            print(f"\nUsing information for: {scheme.scheme_name}")
                            return scheme.details
                    
                    print("\nPlease select a scheme number or press Enter to try another search:")
                    choice = input()
                    if choice.isdigit() and 1 <= int(choice) <= len(search_results):
                        selected_scheme = search_results[int(choice)-1]
                        return selected_scheme.details
                
                # If no matches found
                print("\nNo matching schemes found. Available search terms:")
                # Get some example scheme names from the database
                example_results = self.scheme_tools.search_scheme("scheme")[:5]
                for scheme in example_results:
                    print(f"- {scheme.scheme_name}")
                
                raise ValueError(f"Scheme '{scheme_name}' not found")
                
            return criteria
            
        except Exception as e:
            raise ValueError(f"Error accessing scheme information: {str(e)}")

    def generate_questions(self, criteria: str) -> List[EligibilityQuestion]:
        """Convert eligibility criteria into yes/no questions, strictly based on provided criteria."""
        prompt = f"""
        Convert these exact eligibility criteria into yes/no questions. 
        ONLY create questions from the explicit criteria provided, do not add any assumptions or additional criteria.

        Eligibility Criteria:
        {criteria}

        Rules:
        1. Each question must directly map to a specific criterion in the text
        2. Do not create questions about benefits or scheme features
        3. Do not make assumptions beyond what's explicitly stated
        4. Questions must be answerable with yes/no
        5. Mark a criterion as non-actionable if it's a fundamental requirement (like age, gender)
        
        For each criterion, provide:
        Question: [The yes/no question]
        Criterion: [The exact criterion from the text this question is based on]
        Actionable: [yes/no - can the user take steps to meet this criterion?]
        ---

        Example:
        For criterion "Must be a farmer with less than 2 hectares of land":
        Question: Do you own less than 2 hectares of agricultural land?
        Criterion: Must be a farmer with less than 2 hectares of land
        Actionable: no
        ---
        """
        
        response = self.llm.invoke(prompt).content
        questions = []
        
        for question_block in response.split('---'):
            if not question_block.strip():
                continue
            
            lines = question_block.strip().split('\n')
            q_dict = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    q_dict[key.strip()] = value.strip()
            
            # Only add questions that are based on actual criteria
            if 'Question' in q_dict and 'Criterion' in q_dict:
                # Verify the criterion exists in original text (allowing for minor variations)
                criterion_text = q_dict['Criterion'].lower()
                if any(criterion_text in criteria.lower() or 
                      any(word in criteria.lower() for word in criterion_text.split() if len(word) > 4)):
                    questions.append(EligibilityQuestion(
                        question=q_dict['Question'],
                        criterion=q_dict['Criterion'],
                        is_actionable=q_dict.get('Actionable', 'yes').lower() == 'yes'
                    ))
        
        if not questions:
            raise ValueError("Could not generate valid questions from the eligibility criteria")
        
        return questions

    def check_eligibility(self, scheme_name: str):
        # Get eligibility criteria
        criteria = self.get_scheme_criteria(scheme_name)
        print(f"\nEligibility Criteria for {scheme_name}:")
        print(criteria)
        
        # Generate questions from criteria
        questions = self.generate_questions(criteria)
        
        # Ask questions and collect answers
        print("\nPlease answer the following questions (yes/no):")
        unmet_criteria = []
        
        for question in questions:
            while True:
                answer = input(f"{question.question}: ").lower()
                if answer in ['yes', 'no']:
                    question.answer = answer
                    if answer == 'no':
                        unmet_criteria.append(question)
                    break
                print("Please answer with 'yes' or 'no'")
        
        # Prepare detailed feedback
        is_eligible = len(unmet_criteria) == 0
        
        print(f"\nEligibility Result for {scheme_name}: {'✅ Eligible' if is_eligible else '❌ Not Eligible'}")
        
        if not is_eligible:
            print("\nUnmet Criteria and Required Actions:")
            for q in unmet_criteria:
                print(f"\n• {q.criterion}")
                if q.is_actionable:
                    print("  What you can do:")
                    for step in q.get_action_steps():
                        print(f"  - {step}")
                else:
                    print("  Note: This is a basic eligibility requirement that cannot be changed.")
        
        return is_eligible, unmet_criteria

if __name__ == "__main__":
    checker = EligibilityChecker()
    
    print("\nWelcome to the Scheme Eligibility Checker!")
    print("="*50)
    
    while True:
        # Get scheme name from user
        scheme_name = input("\nEnter scheme name (or 'quit' to exit): ")
        
        if scheme_name.lower() == 'quit':
            break
            
        try:
            print(f"\n{'='*50}")
            print(f"Checking eligibility for: {scheme_name}")
            print(f"{'='*50}")
            is_eligible, unmet_criteria = checker.check_eligibility(scheme_name)
            
            # Ask if user wants to check another scheme
            check_another = input("\nWould you like to check another scheme? (yes/no): ").lower()
            if check_another != 'yes':
                break
                
        except Exception as e:
            print(f"\nError: Could not find information for scheme '{scheme_name}'")
            print("Please check the scheme name and try again.")
