from typing import Dict, List, Any
import re
from dataclasses import dataclass
from enum import Enum

class QueryPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class QueryComponent:
    text: str
    priority: QueryPriority
    context_type: str  # demographic, occupation, financial, needs, etc.

class SchemeQueryBuilder:
    def __init__(self):
        self.occupation_keywords = {
            "Farmer": ["agricultural", "farming", "kisan", "rural", "crop"],
            "Self-employed": ["business", "entrepreneur", "msme", "startup"],
            "Student": ["education", "scholarship", "academic", "student"],
            "Homemaker": ["self-employment", "skill development", "women empowerment"],
            # Add more occupation-specific keywords
        }
        
        self.category_keywords = {
            "SC": ["scheduled caste", "sc category", "dalit"],
            "ST": ["scheduled tribe", "tribal", "st category"],
            "OBC": ["other backward class", "obc category"],
            "Minority": ["minority community", "minority welfare"]
        }
    
    def extract_key_components(self, user_profile: Dict[str, Any]) -> List[QueryComponent]:
        """Extract key components from user profile with priorities."""
        components = []
        
        # Demographic components
        basic_info = user_profile.get("basic_info", {})
        if basic_info:
            components.extend([
                QueryComponent(
                    f"age {basic_info.get('age')}", 
                    QueryPriority.HIGH,
                    "demographic"
                ),
                QueryComponent(
                    f"{basic_info.get('gender', '').lower()}", 
                    QueryPriority.MEDIUM,
                    "demographic"
                ),
                QueryComponent(
                    f"{basic_info.get('category', '').lower()}", 
                    QueryPriority.HIGH,
                    "demographic"
                )
            ])
        
        # Occupation components
        occupation_details = user_profile.get("occupation_details", {})
        if occupation_details:
            occupation = occupation_details.get("type")
            if occupation:
                components.append(
                    QueryComponent(
                        f"{occupation.lower()} schemes",
                        QueryPriority.HIGH,
                        "occupation"
                    )
                )
                # Add occupation-specific keywords
                if occupation in self.occupation_keywords:
                    for keyword in self.occupation_keywords[occupation]:
                        components.append(
                            QueryComponent(
                                keyword,
                                QueryPriority.MEDIUM,
                                "occupation_context"
                            )
                        )
        
        return components
    
    def build_search_queries(self, 
                           user_profile: Dict[str, Any], 
                           open_search_text: str = None) -> List[str]:
        """Build optimized search queries for vector database."""
        components = self.extract_key_components(user_profile)
        queries = []
        
        # Base query from high priority components
        high_priority = " ".join([
            c.text for c in components 
            if c.priority == QueryPriority.HIGH
        ])
        queries.append(high_priority)
        
        # Add open search text if provided
        if open_search_text:
            # Clean and normalize open search text
            cleaned_text = self.clean_search_text(open_search_text)
            queries.append(f"{high_priority} {cleaned_text}")
            
            # Create focused query from open search
            queries.append(f"schemes for {cleaned_text}")
        
        # Add context-specific variations
        occupation_components = [
            c for c in components 
            if c.context_type == "occupation"
        ]
        if occupation_components:
            occ_query = " ".join([c.text for c in occupation_components])
            queries.append(f"government schemes for {occ_query}")
        
        return self.deduplicate_queries(queries)
    
    def clean_search_text(self, text: str) -> str:
        """Clean and normalize search text."""
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Convert to lowercase
        return text.lower()
    
    def deduplicate_queries(self, queries: List[str]) -> List[str]:
        """Remove duplicate and very similar queries."""
        unique_queries = []
        seen_patterns = set()
        
        for query in queries:
            # Create a simplified pattern for comparison
            pattern = re.sub(r'\s+', ' ', query.lower().strip())
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                unique_queries.append(query)
        
        return unique_queries 