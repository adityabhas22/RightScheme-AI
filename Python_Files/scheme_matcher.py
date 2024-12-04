from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
import json
from pinecone import Pinecone
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from openai import OpenAI

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SchemeRecommendation:
    """Detailed recommendation for a government scheme."""
    scheme_name: str
    relevance_score: float
    benefits: List[str]
    eligibility_requirements: Dict[str, str]
    eligibility_status: Dict[str, bool]
    application_process: List[str]
    why_recommended: str
    eligibility_details: Optional[Dict[str, Any]] = None

@dataclass
class UserProfile:
    """User profile with all relevant information for scheme matching."""
    age: int
    gender: str
    category: str
    annual_income: float
    occupation: str
    state: str
    education_level: Optional[str] = None
    specific_needs: List[str] = None

class SchemeCategory(Enum):
    EDUCATION = "Education"
    EMPLOYMENT = "Employment"
    HEALTHCARE = "Healthcare"
    HOUSING = "Housing"
    AGRICULTURE = "Agriculture"
    BUSINESS = "Business"
    SOCIAL_WELFARE = "Social Welfare"

@dataclass
class SchemeMatch:
    scheme_name: str
    relevance_score: float
    category: SchemeCategory
    benefits: List[str]
    eligibility_match: Dict[str, bool]
    application_process: str
    priority_level: str

class SchemeMatcher:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.index = self.pc.Index(os.getenv('PINECONE_INDEX_NAME'))
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create agent with tools
        self.agent_executor = self._create_agent()
        
    def _create_agent(self) -> AgentExecutor:
        """Create an agent with tools for scheme matching."""
        tools = [
            self._extract_scheme_details_tool,
            self._check_eligibility_tool
        ]

        system_message = SystemMessage(
            content="""You are a precise government scheme analyzer. Your job is to:
            1. Extract exact scheme details from text
            2. Strictly evaluate eligibility criteria
            3. Never make assumptions about eligibility
            4. If a criterion is not explicitly mentioned, assume it's not a requirement
            5. Be especially careful with income limits and category restrictions"""
        )

        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    @tool("extract_scheme_details")
    def _extract_scheme_details_tool(self, scheme_text: str) -> str:
        """Extract detailed information about a government scheme from text."""
        try:
            response = self.llm.invoke(
                messages=[{
                    "role": "system",
                    "content": "Extract scheme details in JSON format. Be precise and only include explicitly mentioned information."
                }, {
                    "role": "user",
                    "content": f"Extract details from: {scheme_text}"
                }],
                functions=[{
                    "name": "extract_scheme_details",
                    "description": "Extract scheme details from text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "scheme_name": {"type": "string"},
                            "category": {"type": "string"},
                            "eligibility": {
                                "type": "object",
                                "properties": {
                                    "income_limit": {"type": "number", "nullable": True},
                                    "age_range": {
                                        "type": "object",
                                        "properties": {
                                            "min": {"type": "number"},
                                            "max": {"type": "number"}
                                        },
                                        "nullable": True
                                    },
                                    "category": {"type": "array", "items": {"type": "string"}, "nullable": True},
                                    "gender": {"type": "array", "items": {"type": "string"}, "nullable": True},
                                    "state_specific": {"type": "array", "items": {"type": "string"}, "nullable": True}
                                }
                            },
                            "benefits": {"type": "array", "items": {"type": "string"}},
                            "application_process": {"type": "string", "nullable": True}
                        }
                    }
                }],
                function_call={"name": "extract_scheme_details"}
            )
            
            return response.additional_kwargs["function_call"]["arguments"]
        except Exception as e:
            return json.dumps({
                "error": f"Failed to extract scheme details: {str(e)}",
                "scheme_name": "Unknown",
                "category": "UNKNOWN",
                "eligibility": {},
                "benefits": [],
                "application_process": None
            })

    @tool("check_eligibility")
    def _check_eligibility_tool(self, user_profile: dict, scheme_details: str) -> str:
        """Evaluate if a user meets scheme eligibility criteria."""
        try:
            response = self.llm.invoke(
                messages=[{
                    "role": "system",
                    "content": """You are a STRICT eligibility checker for government schemes.
                    
                    CRITICAL RULES:
                    1. Income limits are ABSOLUTE - if user's income exceeds the limit by ANY amount, return false
                    2. NO EXCEPTIONS to income criteria
                    3. If income limit is mentioned in scheme, you MUST check it
                    4. Return false if income information is unclear
                    5. Category restrictions are STRICT - if scheme is for SC/ST and user is General/OBC, return false
                    6. Age restrictions are ABSOLUTE
                    7. State restrictions must match exactly
                    
                    Example:
                    If scheme says "income below 2 lakh" and user has 2.1 lakh - return false
                    If scheme is for SC/ST and user is OBC - return false
                    If scheme has age limit 60-65 and user is 59 or 66 - return false"""
                }, {
                    "role": "user",
                    "content": f"""Strictly evaluate eligibility:
                    User Profile: {json.dumps(user_profile, indent=2)}
                    Scheme Details: {scheme_details}
                    
                    Remember: ANY income limit violation means automatic disqualification."""
                }],
                functions=[{
                    "name": "evaluate_eligibility",
                    "description": "Strictly evaluate scheme eligibility",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "income_eligible": {
                                "type": "boolean",
                                "description": "True ONLY if user's income is strictly below the scheme's limit"
                            },
                            "age_eligible": {
                                "type": "boolean",
                                "description": "True ONLY if user's age falls exactly within scheme's range"
                            },
                            "category_eligible": {
                                "type": "boolean",
                                "description": "True ONLY if user's category is explicitly included"
                            },
                            "gender_eligible": {
                                "type": "boolean",
                                "description": "True ONLY if user's gender is explicitly included"
                            },
                            "state_eligible": {
                                "type": "boolean",
                                "description": "True ONLY if scheme is available in user's state"
                            },
                            "other_criteria_met": {
                                "type": "boolean",
                                "description": "True ONLY if all other explicit criteria are met"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Explanation of why any criterion was not met"
                            }
                        },
                        "required": ["income_eligible", "age_eligible", "category_eligible", 
                                   "gender_eligible", "state_eligible", "other_criteria_met", "reason"]
                    }
                }],
                function_call={"name": "evaluate_eligibility"}
            )
            
            return response.additional_kwargs["function_call"]["arguments"]
        except Exception as e:
            return json.dumps({
                "income_eligible": False,
                "age_eligible": False,
                "category_eligible": False,
                "gender_eligible": False,
                "state_eligible": False,
                "other_criteria_met": False,
                "reason": f"Error evaluating eligibility: {str(e)}"
            })

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def _generate_search_query(self, user_profile: UserProfile) -> str:
        """Generate optimized search query from user profile."""
        query_parts = [
            f"{user_profile.occupation} schemes",
            f"for {user_profile.gender.lower()} {user_profile.category} category schemes",
            f"schemes for age {user_profile.age}",
            f"{'low' if user_profile.annual_income < 300000 else 'middle' if user_profile.annual_income < 800000 else 'high'} income schemes"
        ]
        
        # Add education-specific terms
        if user_profile.education_level:
            query_parts.append(f"{user_profile.education_level} education support")
            
        # Add specific needs
        if user_profile.specific_needs:
            query_parts.extend(user_profile.specific_needs)
            
        # Add state-specific
        query_parts.append(f"schemes in {user_profile.state}")
        
        return " ".join(query_parts)

    def get_initial_schemes(self, user_profile: UserProfile) -> List[Dict]:
        """Get initial schemes based on semantic search."""
        try:
            search_query = self._generate_search_query(user_profile)
            logger.info(f"Generated search query: {search_query}")
            
            results = self.index.query(
                vector=self._get_embedding(search_query),
                top_k=50,
                include_metadata=True
            )
            
            schemes = []
            for match in results.matches:
                schemes.append({
                    'scheme_name': match.metadata.get('name', 'Unknown Scheme'),
                    'details': match.metadata.get('text', ''),
                    'score': match.score
                })
            
            return schemes
            
        except Exception as e:
            logger.error(f"Error getting initial schemes: {str(e)}")
            return []

    def analyze_schemes_with_llm(self, user_profile: UserProfile, schemes: List[Dict]) -> List[SchemeRecommendation]:
        """Analyze schemes using LLM to get detailed recommendations."""
        try:
            prompt = f"""Analyze these schemes for this user:

User Profile:
- Age: {user_profile.age}
- Gender: {user_profile.gender}
- Category: {user_profile.category}
- Annual Income: ₹{user_profile.annual_income}
- Occupation: {user_profile.occupation}
- State: {user_profile.state}
- Education: {user_profile.education_level or 'Not specified'}
- Specific Needs: {', '.join(user_profile.specific_needs) if user_profile.specific_needs else 'None'}

For each scheme, provide details in this format:
SCHEME NAME: [name]
RELEVANCE: [0-1 score]
WHY RECOMMENDED: [explanation]
BENEFITS:
• [benefit 1]
• [benefit 2]
ELIGIBILITY REQUIREMENTS:
• [requirement 1]: [details]
• [requirement 2]: [details]
HOW TO APPLY:
1. [step 1]
2. [step 2]

Analyze these schemes:
{json.dumps([{'name': s['scheme_name'], 'details': s['details']} for s in schemes], indent=2)}"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in Indian government schemes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            # Parse response into recommendations
            recommendations = []
            scheme_texts = response.choices[0].message.content.split('SCHEME NAME:')
            
            for scheme_text in scheme_texts[1:]:  # Skip first empty split
                try:
                    lines = scheme_text.strip().split('\n')
                    scheme_data = {
                        'name': lines[0].strip(),
                        'relevance': 0.0,
                        'why': '',
                        'benefits': [],
                        'requirements': {},
                        'process': []
                    }
                    
                    current_section = None
                    for line in lines[1:]:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith('RELEVANCE:'):
                            scheme_data['relevance'] = float(line.split(':')[1].strip())
                        elif line.startswith('WHY RECOMMENDED:'):
                            scheme_data['why'] = line.split(':')[1].strip()
                        elif line.startswith('BENEFITS:'):
                            current_section = 'benefits'
                        elif line.startswith('ELIGIBILITY REQUIREMENTS:'):
                            current_section = 'requirements'
                        elif line.startswith('HOW TO APPLY:'):
                            current_section = 'process'
                        elif line.startswith('•') and current_section == 'benefits':
                            scheme_data['benefits'].append(line[1:].strip())
                        elif line.startswith('•') and current_section == 'requirements':
                            key, value = line[1:].split(':', 1)
                            scheme_data['requirements'][key.strip()] = value.strip()
                        elif current_section == 'process' and (line.startswith('1.') or line.startswith('2.')):
                            scheme_data['process'].append(line.split('.', 1)[1].strip())
                    
                    recommendations.append(SchemeRecommendation(
                        scheme_name=scheme_data['name'],
                        relevance_score=scheme_data['relevance'],
                        benefits=scheme_data['benefits'],
                        eligibility_requirements=scheme_data['requirements'],
                        eligibility_status={},  # Will be filled by eligibility checker
                        application_process=scheme_data['process'],
                        why_recommended=scheme_data['why']
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing scheme recommendation: {str(e)}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing schemes: {str(e)}")
            return []

    def get_scheme_recommendations(self, user_profile: UserProfile) -> List[SchemeRecommendation]:
        """Get scheme recommendations with robust hard criteria checking and fallbacks."""
        try:
            # Initialize components
            criteria_checker = HardCriteriaChecker()
            recommendations = []
            error_log = []
            
            # Get initial schemes based on semantic search
            initial_schemes = self.get_initial_schemes(user_profile)
            logger.info(f"Found {len(initial_schemes)} initial schemes through semantic search")
            
            if not initial_schemes:
                logger.warning("No initial schemes found through semantic search")
                return []
            
            # Process each scheme with hard criteria checking
            eligible_schemes = []
            uncertain_schemes = []  # Schemes we couldn't definitively check
            
            for scheme in initial_schemes:
                try:
                    # Extract hard criteria
                    criteria = extract_hard_criteria(scheme['details'], self.openai_client)
                    
                    # Check eligibility
                    is_eligible, check_results = criteria_checker.check_all_criteria(user_profile, criteria)
                    
                    # Store detailed results with the scheme
                    scheme['eligibility_check'] = check_results
                    
                    if is_eligible:
                        if check_results['unknown_criteria']:
                            # If we're unsure about some criteria, keep the scheme but mark it
                            uncertain_schemes.append(scheme)
                            logger.info(f"Scheme {scheme['scheme_name']} added to uncertain list due to: {check_results['unknown_criteria']}")
                        else:
                            eligible_schemes.append(scheme)
                            logger.info(f"Scheme {scheme['scheme_name']} passed all eligibility checks")
                    else:
                        logger.info(f"Scheme {scheme['scheme_name']} failed eligibility checks: {check_results['results']}")
                    
                except Exception as e:
                    # If there's an error processing this scheme, add it to uncertain_schemes
                    error_msg = f"Error processing scheme {scheme.get('scheme_name', 'Unknown')}: {str(e)}"
                    error_log.append(error_msg)
                    logger.error(error_msg)
                    uncertain_schemes.append(scheme)
            
            # Combine eligible and uncertain schemes, prioritizing eligible ones
            combined_schemes = eligible_schemes + uncertain_schemes
            
            if not combined_schemes:
                logger.warning("No schemes passed eligibility checks or were uncertain")
                if error_log:
                    logger.error("Errors encountered during processing: " + "\n".join(error_log))
                return []
            
            # Get detailed recommendations for eligible schemes
            try:
                recommendations = self.analyze_schemes_with_llm(user_profile, combined_schemes)
                
                # Add eligibility check results to recommendations
                for rec in recommendations:
                    matching_scheme = next((s for s in combined_schemes if s['scheme_name'] == rec.scheme_name), None)
                    if matching_scheme and 'eligibility_check' in matching_scheme:
                        rec.eligibility_details = matching_scheme['eligibility_check']
                        
                        # Adjust relevance score based on eligibility certainty
                        if matching_scheme in uncertain_schemes:
                            # Reduce relevance score slightly for uncertain schemes
                            rec.relevance_score *= 0.9
                            rec.why_recommended = "(Note: Some eligibility criteria could not be verified) " + rec.why_recommended
                
                # Sort recommendations by relevance score
                recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
                
            except Exception as e:
                logger.error(f"Error in final analysis: {str(e)}")
                # Fall back to basic recommendations if detailed analysis fails
                recommendations = [
                    SchemeRecommendation(
                        scheme_name=scheme['scheme_name'],
                        relevance_score=0.7,  # Conservative score
                        benefits=[],
                        eligibility_requirements={},
                        eligibility_status={},
                        application_process=[],
                        why_recommended="Basic recommendation due to analysis error"
                    )
                    for scheme in combined_schemes[:5]  # Limit to top 5
                ]
            
            logger.info(f"Final recommendations count: {len(recommendations)}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Critical error in get_scheme_recommendations: {str(e)}")
            return []  # Return empty list as last resort

class EligibilityCheckResult(Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    UNKNOWN = "unknown"  # Used when criteria can't be determined

@dataclass
class SchemeHardCriteria:
    """Hard criteria for scheme eligibility with safe defaults."""
    income_range: Tuple[Optional[float], Optional[float]] = (None, None)
    age_range: Tuple[Optional[int], Optional[int]] = (None, None)
    eligible_genders: List[str] = None
    eligible_states: List[str] = None
    eligible_categories: List[str] = None

    def __post_init__(self):
        """Ensure safe defaults for all fields."""
        if self.eligible_genders is None:
            self.eligible_genders = ["All"]
        if self.eligible_states is None:
            self.eligible_states = ["All"]
        if self.eligible_categories is None:
            self.eligible_categories = ["All"]

class HardCriteriaChecker:
    """Checks hard criteria with robust error handling and logging."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_income(self, user_income: float, criteria: SchemeHardCriteria) -> Tuple[EligibilityCheckResult, str]:
        """Check income eligibility with detailed error handling."""
        try:
            min_income, max_income = criteria.income_range
            
            if min_income is None and max_income is None:
                return EligibilityCheckResult.ELIGIBLE, "No income restrictions specified"
                
            if user_income is None:
                return EligibilityCheckResult.UNKNOWN, "User income not provided"
                
            if min_income is not None and user_income < min_income:
                return EligibilityCheckResult.NOT_ELIGIBLE, f"Income below minimum requirement of {min_income}"
                
            if max_income is not None and user_income > max_income:
                return EligibilityCheckResult.NOT_ELIGIBLE, f"Income above maximum limit of {max_income}"
                
            return EligibilityCheckResult.ELIGIBLE, "Income within acceptable range"
            
        except Exception as e:
            self.logger.warning(f"Error checking income eligibility: {str(e)}")
            return EligibilityCheckResult.UNKNOWN, f"Could not determine income eligibility: {str(e)}"

    def check_age(self, user_age: int, criteria: SchemeHardCriteria) -> Tuple[EligibilityCheckResult, str]:
        """Check age eligibility with detailed error handling."""
        try:
            min_age, max_age = criteria.age_range
            
            if min_age is None and max_age is None:
                return EligibilityCheckResult.ELIGIBLE, "No age restrictions specified"
                
            if user_age is None:
                return EligibilityCheckResult.UNKNOWN, "User age not provided"
                
            if min_age is not None and user_age < min_age:
                return EligibilityCheckResult.NOT_ELIGIBLE, f"Age below minimum requirement of {min_age}"
                
            if max_age is not None and user_age > max_age:
                return EligibilityCheckResult.NOT_ELIGIBLE, f"Age above maximum limit of {max_age}"
                
            return EligibilityCheckResult.ELIGIBLE, "Age within acceptable range"
            
        except Exception as e:
            self.logger.warning(f"Error checking age eligibility: {str(e)}")
            return EligibilityCheckResult.UNKNOWN, f"Could not determine age eligibility: {str(e)}"

    def check_gender(self, user_gender: str, criteria: SchemeHardCriteria) -> Tuple[EligibilityCheckResult, str]:
        """Check gender eligibility with detailed error handling."""
        try:
            if not user_gender:
                return EligibilityCheckResult.UNKNOWN, "User gender not provided"
                
            if "All" in criteria.eligible_genders:
                return EligibilityCheckResult.ELIGIBLE, "Scheme open to all genders"
                
            if user_gender in criteria.eligible_genders:
                return EligibilityCheckResult.ELIGIBLE, f"Gender ({user_gender}) eligible"
                
            return EligibilityCheckResult.NOT_ELIGIBLE, f"Scheme only open to: {', '.join(criteria.eligible_genders)}"
            
        except Exception as e:
            self.logger.warning(f"Error checking gender eligibility: {str(e)}")
            return EligibilityCheckResult.UNKNOWN, f"Could not determine gender eligibility: {str(e)}"

    def check_state(self, user_state: str, criteria: SchemeHardCriteria) -> Tuple[EligibilityCheckResult, str]:
        """Check state eligibility with detailed error handling."""
        try:
            if not user_state:
                return EligibilityCheckResult.UNKNOWN, "User state not provided"
                
            if "All" in criteria.eligible_states:
                return EligibilityCheckResult.ELIGIBLE, "Scheme available in all states"
                
            if user_state in criteria.eligible_states:
                return EligibilityCheckResult.ELIGIBLE, f"State ({user_state}) eligible"
                
            return EligibilityCheckResult.NOT_ELIGIBLE, f"Scheme only available in: {', '.join(criteria.eligible_states)}"
            
        except Exception as e:
            self.logger.warning(f"Error checking state eligibility: {str(e)}")
            return EligibilityCheckResult.UNKNOWN, f"Could not determine state eligibility: {str(e)}"

    def check_category(self, user_category: str, criteria: SchemeHardCriteria) -> Tuple[EligibilityCheckResult, str]:
        """Check category eligibility with detailed error handling."""
        try:
            if not user_category:
                return EligibilityCheckResult.UNKNOWN, "User category not provided"
                
            if "All" in criteria.eligible_categories:
                return EligibilityCheckResult.ELIGIBLE, "Scheme open to all categories"
                
            if user_category in criteria.eligible_categories:
                return EligibilityCheckResult.ELIGIBLE, f"Category ({user_category}) eligible"
                
            return EligibilityCheckResult.NOT_ELIGIBLE, f"Scheme only open to: {', '.join(criteria.eligible_categories)}"
            
        except Exception as e:
            self.logger.warning(f"Error checking category eligibility: {str(e)}")
            return EligibilityCheckResult.UNKNOWN, f"Could not determine category eligibility: {str(e)}"

    def check_all_criteria(self, user_profile: 'UserProfile', criteria: SchemeHardCriteria) -> Tuple[bool, Dict[str, Any]]:
        """Check all hard criteria with comprehensive error handling and logging."""
        results = {}
        unknown_criteria = []
        
        # Check each criterion
        checks = {
            "income": (self.check_income, user_profile.annual_income),
            "age": (self.check_age, user_profile.age),
            "gender": (self.check_gender, user_profile.gender),
            "state": (self.check_state, user_profile.state),
            "category": (self.check_category, user_profile.category)
        }
        
        for criterion_name, (check_func, user_value) in checks.items():
            result, message = check_func(user_value, criteria)
            results[criterion_name] = {
                "status": result,
                "message": message,
                "user_value": user_value
            }
            
            if result == EligibilityCheckResult.UNKNOWN:
                unknown_criteria.append(criterion_name)
        
        # Log detailed results
        self.logger.info(f"Eligibility Check Results:")
        for criterion, result in results.items():
            self.logger.info(f"{criterion}: {result['status'].value} - {result['message']}")
        
        # Determine overall eligibility
        # If any criterion is definitely NOT_ELIGIBLE, return False
        # If all criteria are ELIGIBLE or UNKNOWN, return True (benefit of doubt)
        # This ensures we don't exclude schemes when we're unsure
        definitely_ineligible = any(
            result["status"] == EligibilityCheckResult.NOT_ELIGIBLE 
            for result in results.values()
        )
        
        is_eligible = not definitely_ineligible
        
        if unknown_criteria:
            self.logger.warning(f"Could not determine eligibility for criteria: {', '.join(unknown_criteria)}")
        
        return is_eligible, {
            "results": results,
            "unknown_criteria": unknown_criteria,
            "is_eligible": is_eligible,
            "timestamp": datetime.now().isoformat()
        }

def extract_hard_criteria(scheme_text: str, openai_client) -> SchemeHardCriteria:
    """Extract hard criteria with fallback mechanisms."""
    try:
        prompt = """Extract the exact eligibility criteria from this scheme text.
        If a criterion is not explicitly mentioned, mark it as null or ["All"].
        
        Return in this JSON format:
        {
            "income_range": [min_income, max_income],
            "age_range": [min_age, max_age],
            "eligible_genders": ["Male"/"Female"/"All"],
            "eligible_states": ["State1", "State2"] or ["All"],
            "eligible_categories": ["SC", "ST", "OBC", "General"] or ["All"]
        }
        
        Scheme text:
        {text}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a precise eligibility criteria extractor."},
                {"role": "user", "content": prompt.format(text=scheme_text)}
            ],
            response_format={ "type": "json_object" }
        )
        
        criteria_dict = json.loads(response.choices[0].message.content)
        return SchemeHardCriteria(**criteria_dict)
        
    except Exception as e:
        logger.error(f"Error extracting hard criteria: {str(e)}")
        # Return default criteria (all inclusive) to avoid excluding schemes when extraction fails
        return SchemeHardCriteria()