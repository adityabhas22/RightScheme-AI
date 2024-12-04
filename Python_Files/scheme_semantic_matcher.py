from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
from dataclasses import dataclass
import re
import json

# Load environment variables
load_dotenv()

@dataclass
class UserProfile:
    """User profile with all relevant information for scheme matching."""
    age: int
    gender: str
    category: str
    annual_income: float
    occupation: str
    occupation_details: Dict[str, Any]
    state: str
    education_level: str
    specific_needs: List[str]
    interests: str
    marital_status: Optional[str] = None

class SchemeRecommendation(BaseModel):
    """Schema for recommended schemes."""
    scheme_name: str
    relevance_score: float
    benefits: List[str]
    eligibility_requirements: Dict[str, str]  # requirement type -> specific requirement
    eligibility_status: Dict[str, bool]  # requirement type -> whether user meets it
    application_process: List[str]  # Step by step process
    why_recommended: str

class SemanticSchemeMatcher:
    def __init__(self):
        """Initialize with Pinecone and OpenAI."""
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.index = self.pc.Index(os.getenv('PINECONE_INDEX_NAME'))
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.MIN_RELEVANCE_SCORE = 0.7

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using OpenAI."""
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return np.array(response.data[0].embedding, dtype='float32')

    def is_scheme_applicable_for_state(self, scheme_details: str, user_state: str) -> bool:
        """Check if scheme is applicable for user's state."""
        scheme_details = scheme_details.lower()
        state_name = user_state.lower()
        
        # Central scheme indicators
        central_indicators = [
            "central scheme", 
            "centrally sponsored", 
            "nationwide",
            "all states",
            "pan india",
            "government of india"
        ]
        
        # Check for central schemes
        if any(indicator in scheme_details for indicator in central_indicators):
            return True
            
        # Check for state-specific schemes
        if state_name in scheme_details:
            return True
            
        # Check for other state mentions
        indian_states = {
            "andhra pradesh", "arunachal pradesh", "assam", "bihar", 
            "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh", 
            "jharkhand", "karnataka", "kerala", "madhya pradesh", 
            "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland", 
            "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", 
            "telangana", "tripura", "uttar pradesh", "uttarakhand", 
            "west bengal"
        }
        
        for state in indian_states:
            if state != state_name and state in scheme_details:
                return False
                
        return True

    def create_search_query(self, user_profile: UserProfile) -> str:
        """Create a comprehensive search query from user profile."""
        query_parts = [
            user_profile.interests,
            f"schemes for {user_profile.occupation}",
            f"{user_profile.category} category schemes",
            f"schemes for {user_profile.gender.lower()}"
        ]
        
        # Add occupation-specific terms
        if user_profile.occupation == "Student":
            query_parts.append("education scholarship academic")
        elif user_profile.occupation == "Farmer":
            query_parts.append("agricultural farming subsidy krishi")
        elif user_profile.occupation == "Self-employed":
            query_parts.append("business entrepreneurship startup msme")
            
        # Add specific needs
        if user_profile.specific_needs:
            query_parts.extend(user_profile.specific_needs)
            
        return " ".join(query_parts)

    def get_initial_schemes(self, user_profile: UserProfile) -> List[Dict]:
        """Get initial set of potentially relevant schemes."""
        search_query = self.create_search_query(user_profile)
        query_embedding = self.generate_embedding(search_query)
        
        results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=20,
            include_metadata=True
        )
        
        filtered_schemes = []
        chunks_to_identify = []
        
        # First collect all relevant chunks
        for match in results.matches:
            if match.score >= self.MIN_RELEVANCE_SCORE:
                text = match.metadata.get("text", "")
                if self.is_scheme_applicable_for_state(text, user_profile.state):
                    chunks_to_identify.append(text)
        
        # Use LLM to identify scheme names from chunks
        if chunks_to_identify:
            scheme_names = self._identify_schemes_with_llm(chunks_to_identify)
            
            # Create filtered schemes with identified names
            for text, name in zip(chunks_to_identify, scheme_names):
                if name:  # Only add if we got a valid name
                    filtered_schemes.append({
                        "scheme_name": name,
                        "details": text,
                        "score": float(match.score)
                    })
        
        return filtered_schemes

    def _identify_schemes_with_llm(self, texts: List[str]) -> List[str]:
        """Use LLM to identify scheme names from text chunks."""
        prompt = """For each text chunk below, identify the official government scheme name. 
        If multiple schemes are mentioned, identify the main scheme being discussed.
        If no specific scheme name is found, return "Unknown Scheme".
        
        Return only the scheme names, one per line.
        
        Text chunks:
        ---
        {}
        ---"""
        
        # Join texts with clear separators
        formatted_texts = "\n\n###\n\n".join(texts)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in identifying Indian government schemes."},
                    {"role": "user", "content": prompt.format(formatted_texts)}
                ],
                temperature=0.3  # Lower temperature for more consistent naming
            )
            
            # Split response into lines and clean
            scheme_names = [
                name.strip() 
                for name in response.choices[0].message.content.strip().split('\n')
                if name.strip()
            ]
            
            # Ensure we have same number of names as input texts
            while len(scheme_names) < len(texts):
                scheme_names.append("Unknown Scheme")
                
            return scheme_names
            
        except Exception as e:
            print(f"Error identifying scheme names: {e}")
            return ["Unknown Scheme"] * len(texts)

    def analyze_schemes_with_llm(self, user_profile: UserProfile, schemes: List[Dict]) -> List[SchemeRecommendation]:
        """Analyze schemes using LLM to find best matches."""
        prompt = f"""You are an expert in Indian government schemes. Analyze these schemes for this user:

User Profile:
- Age: {user_profile.age}
- Gender: {user_profile.gender}
- Category: {user_profile.category}
- Annual Income: ₹{user_profile.annual_income}
- Occupation: {user_profile.occupation}
- State: {user_profile.state}
- Education: {user_profile.education_level}
- Marital Status: {user_profile.marital_status}
- Specific Needs: {', '.join(user_profile.specific_needs) if user_profile.specific_needs else 'None'}
- Looking for: {user_profile.interests}

CRITICAL RULES:
1. Income limits are ABSOLUTE - if user's income exceeds the scheme's limit by ANY amount, DO NOT include the scheme
2. NO EXCEPTIONS to income criteria
3. If income limit is mentioned in scheme, you MUST check it
4. If income information is unclear, assume user is not eligible
5. Only return schemes where the user meets ALL eligibility criteria, especially income limits

For each ELIGIBLE scheme, provide details in this exact format:

SCHEME NAME: [Exact official name of the scheme]
RELEVANCE: [Score between 0 and 1]
WHY RECOMMENDED: [Brief explanation of why this scheme matches the user's needs]
BENEFITS:
• [List each major benefit]
• [Include monetary benefits if any]
ELIGIBILITY:
• Age Requirement: [Specify exact requirement] | [Yes/No based on user's eligibility]
• Income Limit: [Specify exact limit] | [Yes/No based on user's eligibility]
• Category: [Specify eligible categories] | [Yes/No based on user's eligibility]
• Occupation: [Specify if any] | [Yes/No based on user's eligibility]
• State: [Specify eligible states] | [Yes/No based on user's eligibility]
HOW TO APPLY:
1. [Step by step process]
2. [Include required documents]
3. [Where to apply]

Analyze these schemes:
{json.dumps([{'name': s['scheme_name'], 'details': s['details']} for s in schemes], indent=2)}

Return details for only the top 5 most relevant schemes where the user meets ALL eligibility criteria, especially income limits.
DO NOT include any schemes where the user's income exceeds the scheme's limit.
Separate each scheme with ---"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in Indian government schemes with strict attention to eligibility criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            # Get the response text
            analysis = response.choices[0].message.content
            
            # Parse into recommendations
            recommendations = []
            schemes = [s.strip() for s in analysis.split('---') if s.strip()]
            
            for scheme_text in schemes:
                try:
                    lines = scheme_text.split('\n')
                    scheme_data = {
                        'name': '',
                        'score': 0.0,
                        'reason': '',
                        'benefits': [],
                        'eligibility_requirements': {},
                        'eligibility_status': {},
                        'process': []
                    }
                    
                    current_section = None
                    income_eligible = None  # Track income eligibility, None means not yet determined
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        if line.startswith('SCHEME NAME:'):
                            scheme_data['name'] = line.replace('SCHEME NAME:', '').strip()
                        elif line.startswith('RELEVANCE:'):
                            try:
                                scheme_data['score'] = float(line.replace('RELEVANCE:', '').strip())
                            except:
                                scheme_data['score'] = 0.5
                        elif line.startswith('WHY RECOMMENDED:'):
                            scheme_data['reason'] = line.replace('WHY RECOMMENDED:', '').strip()
                        elif line.startswith('BENEFITS:'):
                            current_section = 'benefits'
                        elif line.startswith('ELIGIBILITY:'):
                            current_section = 'eligibility'
                        elif line.startswith('HOW TO APPLY:'):
                            current_section = 'process'
                        elif line.startswith('•') or line.startswith('*'):
                            if current_section == 'benefits':
                                scheme_data['benefits'].append(line.replace('•', '').replace('*', '').strip())
                            elif current_section == 'eligibility':
                                # Split eligibility criteria and status
                                parts = line.replace('•', '').replace('*', '').strip().split('|')
                                if len(parts) == 2:
                                    criterion, status = parts[0].split(':')
                                    criterion = criterion.strip()
                                    requirement = status.strip()
                                    status = parts[1].strip().lower() == 'yes'
                                    
                                    # Check if this is income criterion
                                    if 'income' in criterion.lower():
                                        income_eligible = status
                                    
                                    scheme_data['eligibility_requirements'][criterion] = requirement
                                    scheme_data['eligibility_status'][criterion] = status
                        elif line.startswith(('1.', '2.', '3.')) and current_section == 'process':
                            scheme_data['process'].append(line.strip())
                    
                    # Only add scheme if it has a valid name and either:
                    # 1. Income is explicitly eligible (income_eligible is True)
                    # 2. No income criteria mentioned (income_eligible is None)
                    if scheme_data['name'] and (income_eligible is True or income_eligible is None):
                        recommendations.append(SchemeRecommendation(
                            scheme_name=scheme_data['name'],
                            relevance_score=scheme_data['score'],
                            benefits=scheme_data['benefits'],
                            eligibility_requirements=scheme_data['eligibility_requirements'],
                            eligibility_status=scheme_data['eligibility_status'],
                            application_process=scheme_data['process'],
                            why_recommended=scheme_data['reason']
                        ))
                        
                except Exception as parse_error:
                    print(f"Error parsing scheme: {parse_error}")
                    continue
            
            return recommendations
            
        except Exception as e:
            print(f"Error in analyze_schemes_with_llm: {e}")
            return []

    def get_scheme_recommendations(self, user_profile: UserProfile) -> List[SchemeRecommendation]:
        """Main method to get scheme recommendations."""
        # Get initial schemes based on semantic search
        initial_schemes = self.get_initial_schemes(user_profile)
        
        # If no schemes found, return empty list
        if not initial_schemes:
            return []
            
        # Analyze schemes with LLM to get final recommendations
        recommendations = self.analyze_schemes_with_llm(user_profile, initial_schemes)
        
        return recommendations 