from typing import Dict, List, Optional
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

load_dotenv()

@dataclass
class UserProfile:
    age: int
    gender: str
    category: str
    annual_income: float
    occupation: str
    state: str
    education_level: Optional[str] = None
    marital_status: Optional[str] = None
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

    def get_matching_schemes(self, user_profile: UserProfile) -> List[SchemeMatch]:
        """Get matching schemes using function calling agent."""
        try:
            matches = []
            search_query = self._generate_search_query(user_profile)
            results = self.index.query(
                vector=self._get_embedding(search_query),
                top_k=50,
                include_metadata=True
            )
            
            user_profile_dict = {
                "age": user_profile.age,
                "gender": user_profile.gender,
                "category": user_profile.category,
                "annual_income": user_profile.annual_income,
                "occupation": user_profile.occupation,
                "state": user_profile.state,
                "education_level": user_profile.education_level
            }
            
            for result in results.matches:
                try:
                    scheme_text = result.metadata.get("text", "")
                    
                    # Extract scheme details using function calling
                    scheme_details = json.loads(self._extract_scheme_details_tool(scheme_text))
                    if "error" in scheme_details:
                        continue
                        
                    # Check eligibility using function calling
                    eligibility_results = json.loads(self._check_eligibility_tool(
                        user_profile_dict, 
                        json.dumps(scheme_details)
                    ))
                    if "error" in eligibility_results:
                        continue
                    
                    if all(eligibility_results.values()):
                        try:
                            match = SchemeMatch(
                                scheme_name=scheme_details["scheme_name"],
                                category=SchemeCategory[scheme_details["category"].upper()],
                                benefits=scheme_details["benefits"],
                                eligibility_match=eligibility_results,
                                application_process=scheme_details.get("application_process", ""),
                                relevance_score=result.score,
                                priority_level=self._determine_priority_level(result.score)
                            )
                            matches.append(match)
                        except (KeyError, ValueError) as e:
                            continue
                            
                except Exception as e:
                    continue
            
            return sorted(matches, key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            print(f"Error in get_matching_schemes: {str(e)}")
            return []