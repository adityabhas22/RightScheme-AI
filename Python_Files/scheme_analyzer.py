from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import re
from Python_Files.translation_utils import translate_text

@dataclass
class SchemeInfo:
    scheme_name: str
    description: str
    benefits: List[str]
    eligibility_criteria: Dict[str, Any]
    application_process: str
    required_documents: List[str]
    success_factors: List[str]
    warnings: List[str]

class UserFriendlyAnalysis:
    def __init__(self, scheme_name: str):
        self.scheme_name = scheme_name
        self.summary = ""
        self.key_benefits = []
        self.eligibility_status = ""
        self.eligibility_details = {}
        self.application_process = ""
        self.next_steps = []
        self.required_documents = []
        self.success_factors = []
        self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary format."""
        return {
            "scheme_name": self.scheme_name,
            "summary": self.summary,
            "key_benefits": self.key_benefits,
            "eligibility_status": self.eligibility_status,
            "eligibility_details": self.eligibility_details,
            "application_process": self.application_process,
            "next_steps": self.next_steps,
            "required_documents": self.required_documents,
            "success_factors": self.success_factors,
            "warnings": self.warnings
        }
    
    def to_bilingual_dict(self, target_lang: str) -> Dict[str, Dict[str, Any]]:
        """Convert analysis to bilingual dictionary format."""
        return {
            "scheme_name": {
                "en": self.scheme_name,
                target_lang: translate_text(self.scheme_name, target_lang=target_lang)
            },
            "summary": {
                "en": self.summary,
                target_lang: translate_text(self.summary, target_lang=target_lang)
            },
            "key_benefits": {
                "en": self.key_benefits,
                target_lang: [translate_text(benefit, target_lang=target_lang) for benefit in self.key_benefits]
            },
            "eligibility_status": {
                "en": self.eligibility_status,
                target_lang: translate_text(self.eligibility_status, target_lang=target_lang)
            },
            "eligibility_details": {
                "en": self.eligibility_details,
                target_lang: {translate_text(k, target_lang=target_lang): v for k, v in self.eligibility_details.items()}
            },
            "application_process": {
                "en": self.application_process,
                target_lang: translate_text(self.application_process, target_lang=target_lang)
            },
            "next_steps": {
                "en": self.next_steps,
                target_lang: [translate_text(step, target_lang=target_lang) for step in self.next_steps]
            },
            "required_documents": {
                "en": self.required_documents,
                target_lang: [translate_text(doc, target_lang=target_lang) for doc in self.required_documents]
            },
            "success_factors": {
                "en": self.success_factors,
                target_lang: [translate_text(factor, target_lang=target_lang) for factor in self.success_factors]
            },
            "warnings": {
                "en": self.warnings,
                target_lang: [translate_text(warning, target_lang=target_lang) for warning in self.warnings]
            }
        }

class SchemeAnalyzer:
    def extract_scheme_info(self, scheme_text: str) -> Optional[SchemeInfo]:
        """Extract structured information from scheme text."""
        try:
            # Basic extraction of scheme name (first line or section)
            lines = scheme_text.split('\n')
            scheme_name = lines[0].strip()
            
            # Extract description (usually the first paragraph)
            description = ""
            for line in lines[1:]:
                if line.strip():
                    description = line.strip()
                    break
            
            # Extract benefits (look for bullet points or numbered lists)
            benefits = []
            for line in lines:
                line = line.strip()
                if line.startswith('•') or line.startswith('-') or re.match(r'^\d+\.', line):
                    benefits.append(line.lstrip('•-123456789. '))
            
            # Basic eligibility criteria extraction
            eligibility_criteria = {}
            in_eligibility_section = False
            current_criterion = ""
            
            for line in lines:
                line = line.strip().lower()
                if 'eligibility' in line or 'criteria' in line:
                    in_eligibility_section = True
                    continue
                if in_eligibility_section and line:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        eligibility_criteria[key.strip()] = value.strip()
                    else:
                        current_criterion += line + " "
            
            if current_criterion:
                eligibility_criteria['general'] = current_criterion.strip()
            
            # Extract application process
            application_process = ""
            in_application_section = False
            
            for line in lines:
                if 'how to apply' in line.lower() or 'application process' in line.lower():
                    in_application_section = True
                    continue
                if in_application_section and line.strip():
                    application_process += line.strip() + " "
            
            # Extract required documents
            required_documents = []
            in_documents_section = False
            
            for line in lines:
                if 'required document' in line.lower() or 'document required' in line.lower():
                    in_documents_section = True
                    continue
                if in_documents_section and line.strip():
                    if line.startswith('•') or line.startswith('-'):
                        required_documents.append(line.lstrip('•- '))
            
            # Extract success factors and warnings
            success_factors = []
            warnings = []
            
            for line in lines:
                line = line.strip()
                if 'important' in line.lower() or 'warning' in line.lower() or 'note:' in line.lower():
                    warnings.append(line)
                elif 'tip' in line.lower() or 'advice' in line.lower() or 'recommend' in line.lower():
                    success_factors.append(line)
            
            return SchemeInfo(
                scheme_name=scheme_name,
                description=description,
                benefits=benefits,
                eligibility_criteria=eligibility_criteria,
                application_process=application_process,
                required_documents=required_documents,
                success_factors=success_factors,
                warnings=warnings
            )
            
        except Exception as e:
            print(f"Error extracting scheme info: {str(e)}")
            return None

    def analyze_eligibility(self, scheme_info: SchemeInfo, user_profile: Dict[str, Any]) -> Dict[str, bool]:
        """Analyze if user meets eligibility criteria."""
        try:
            eligibility_results = {}
            
            # Extract age requirements
            for criterion, value in scheme_info.eligibility_criteria.items():
                criterion_lower = criterion.lower()
                if 'age' in criterion_lower:
                    try:
                        # Extract numbers from the criterion
                        numbers = re.findall(r'\d+', value)
                        if len(numbers) >= 2:
                            min_age = int(numbers[0])
                            max_age = int(numbers[1])
                            user_age = user_profile.get('age', 0)
                            eligibility_results[criterion] = min_age <= user_age <= max_age
                    except:
                        eligibility_results[criterion] = True  # If can't parse, assume eligible
                
                # Check income criteria
                elif 'income' in criterion_lower:
                    try:
                        # Extract numbers from the criterion
                        numbers = re.findall(r'\d+', value)
                        if numbers:
                            max_income = float(numbers[0])
                            user_income = user_profile.get('annual_income', 0)
                            eligibility_results[criterion] = user_income <= max_income
                    except:
                        eligibility_results[criterion] = True
                
                # Check category/caste criteria
                elif any(word in criterion_lower for word in ['category', 'caste', 'sc', 'st', 'obc']):
                    user_category = user_profile.get('category', '').lower()
                    if user_category:
                        eligibility_results[criterion] = user_category in value.lower()
                
                # Check gender criteria
                elif 'gender' in criterion_lower:
                    user_gender = user_profile.get('gender', '').lower()
                    if user_gender:
                        eligibility_results[criterion] = user_gender in value.lower()
                
                # Check occupation criteria
                elif any(word in criterion_lower for word in ['occupation', 'profession', 'employment']):
                    user_occupation = user_profile.get('occupation', '').lower()
                    if user_occupation:
                        eligibility_results[criterion] = user_occupation in value.lower()
                
                # Default to True for criteria we can't specifically check
                else:
                    eligibility_results[criterion] = True
            
            return eligibility_results
            
        except Exception as e:
            print(f"Error analyzing eligibility: {str(e)}")
            return {}

    def calculate_needs_match(self, scheme_info: SchemeInfo, user_needs: List[str]) -> float:
        """Calculate how well scheme matches user's needs."""
        try:
            if not user_needs:
                return 0.5  # Default match if no needs specified
            
            matched_needs = 0
            total_needs = len(user_needs)
            
            # Convert everything to lowercase for comparison
            scheme_text = ' '.join([
                scheme_info.description.lower(),
                ' '.join(b.lower() for b in scheme_info.benefits),
                ' '.join(str(v).lower() for v in scheme_info.eligibility_criteria.values())
            ])
            
            for need in user_needs:
                need_lower = need.lower()
                if need_lower in scheme_text:
                    matched_needs += 1
                # Check for related terms
                elif any(related in scheme_text for related in self._get_related_terms(need_lower)):
                    matched_needs += 0.5
            
            return matched_needs / total_needs
            
        except Exception as e:
            print(f"Error calculating needs match: {str(e)}")
            return 0.0

    def calculate_category_relevance(self, scheme_info: SchemeInfo, user_profile: Dict[str, Any]) -> float:
        """Calculate how relevant scheme is for user's category."""
        try:
            relevance_score = 0.5  # Default middle score
            
            # Check if scheme specifically mentions user's category
            user_category = user_profile.get('category', '').lower()
            scheme_text = ' '.join([
                scheme_info.description.lower(),
                ' '.join(str(v).lower() for v in scheme_info.eligibility_criteria.values())
            ])
            
            if user_category in scheme_text:
                relevance_score = 1.0
            elif any(cat in scheme_text for cat in ['general', 'all categories', 'any category']):
                relevance_score = 0.8
            elif any(cat in scheme_text for cat in ['sc', 'st', 'obc', 'minority']) and user_category in ['sc', 'st', 'obc', 'minority']:
                relevance_score = 0.9
            
            return relevance_score
            
        except Exception as e:
            print(f"Error calculating category relevance: {str(e)}")
            return 0.5

    def calculate_accessibility(self, scheme_info: SchemeInfo, user_profile: Dict[str, Any]) -> float:
        """Calculate how accessible the scheme is for the user."""
        try:
            accessibility_score = 0.0
            factors_checked = 0
            
            # Check income requirements
            income_mentioned = False
            for criterion in scheme_info.eligibility_criteria:
                if 'income' in criterion.lower():
                    income_mentioned = True
                    user_income = user_profile.get('annual_income', 0)
                    try:
                        max_income = float(re.findall(r'\d+', scheme_info.eligibility_criteria[criterion])[0])
                        if user_income <= max_income:
                            accessibility_score += 1
                    except:
                        accessibility_score += 0.5  # If can't parse income requirement
                    factors_checked += 1
            
            if not income_mentioned:
                accessibility_score += 0.8  # No income restriction is generally good
                factors_checked += 1
            
            # Check document requirements
            doc_score = 1.0
            if scheme_info.required_documents:
                doc_score = 1.0 - (len(scheme_info.required_documents) * 0.1)  # Reduce score for more documents
                doc_score = max(0.2, doc_score)  # Don't go below 0.2
            accessibility_score += doc_score
            factors_checked += 1
            
            # Check application process complexity
            process_score = 1.0
            process_text = scheme_info.application_process.lower()
            complexity_indicators = ['visit office', 'in person', 'multiple steps', 'verification']
            for indicator in complexity_indicators:
                if indicator in process_text:
                    process_score -= 0.2
            process_score = max(0.2, process_score)
            accessibility_score += process_score
            factors_checked += 1
            
            return accessibility_score / factors_checked if factors_checked > 0 else 0.5
            
        except Exception as e:
            print(f"Error calculating accessibility: {str(e)}")
            return 0.5

    def _get_related_terms(self, need: str) -> List[str]:
        """Get related terms for a given need."""
        try:
            related_terms_dict = {
                'financial': ['money', 'loan', 'subsidy', 'grant', 'aid', 'assistance'],
                'education': ['study', 'school', 'college', 'university', 'scholarship', 'learning'],
                'healthcare': ['medical', 'health', 'hospital', 'treatment', 'medicine'],
                'housing': ['home', 'house', 'accommodation', 'shelter', 'residence'],
                'employment': ['job', 'work', 'career', 'business', 'self-employment', 'occupation'],
                'agriculture': ['farming', 'crop', 'irrigation', 'farm', 'agricultural'],
                'skill': ['training', 'development', 'workshop', 'vocational', 'apprenticeship']
            }
            
            for category, terms in related_terms_dict.items():
                if need in terms or category in need:
                    return terms
            
            return []
            
        except Exception as e:
            print(f"Error matching needs to category: {str(e)}")
            return []

    def generate_comprehensive_analysis(
        self,
        scheme_info: SchemeInfo,
        user_profile: Dict[str, Any],
        eligibility_results: Dict[str, bool],
        needs_match: float,
        category_relevance: float,
        accessibility: float
    ) -> UserFriendlyAnalysis:
        """Generate comprehensive analysis with all components."""
        try:
            analysis = UserFriendlyAnalysis(scheme_info.scheme_name)
            
            # Generate summary
            eligible_count = sum(1 for v in eligibility_results.values() if v)
            total_criteria = len(eligibility_results)
            eligibility_percentage = (eligible_count / total_criteria * 100) if total_criteria > 0 else 0
            
            summary_parts = []
            if eligibility_percentage >= 80:
                summary_parts.append("You appear to be highly eligible for this scheme.")
            elif eligibility_percentage >= 50:
                summary_parts.append("You meet some of the eligibility criteria for this scheme.")
            else:
                summary_parts.append("You might face some challenges qualifying for this scheme.")
            
            if needs_match >= 0.7:
                summary_parts.append("This scheme strongly aligns with your needs.")
            elif needs_match >= 0.4:
                summary_parts.append("This scheme partially addresses your requirements.")
            
            if accessibility >= 0.7:
                summary_parts.append("The application process appears to be straightforward.")
            elif accessibility < 0.4:
                summary_parts.append("The application process might be somewhat complex.")
            
            analysis.summary = " ".join(summary_parts)
            
            # Add key benefits
            analysis.key_benefits = scheme_info.benefits[:5]  # Top 5 benefits
            
            # Generate eligibility status
            if eligibility_percentage >= 80:
                analysis.eligibility_status = "You meet most eligibility criteria."
            elif eligibility_percentage >= 50:
                analysis.eligibility_status = "You partially meet the eligibility criteria."
            else:
                analysis.eligibility_status = "You may need to review the eligibility criteria carefully."
            
            # Add detailed eligibility results
            analysis.eligibility_details = eligibility_results
            
            # Process application steps
            analysis.application_process = scheme_info.application_process
            
            # Generate next steps
            next_steps = []
            if scheme_info.required_documents:
                next_steps.append("Gather the required documents")
            if "online" in scheme_info.application_process.lower():
                next_steps.append("Visit the official website to start your application")
            if "office" in scheme_info.application_process.lower():
                next_steps.append("Visit the nearest office with required documents")
            next_steps.append("Submit your application as per the process")
            next_steps.append("Keep track of your application status")
            analysis.next_steps = next_steps
            
            # Add required documents
            analysis.required_documents = scheme_info.required_documents
            
            # Add success factors
            analysis.success_factors = scheme_info.success_factors
            if not analysis.success_factors:
                analysis.success_factors = [
                    "Keep all documents ready before starting the application",
                    "Double-check all information before submission",
                    "Follow up regularly on your application status",
                    "Keep copies of all submitted documents"
                ]
            
            # Add warnings
            analysis.warnings = scheme_info.warnings
            if not analysis.warnings and eligibility_percentage < 50:
                analysis.warnings.append(
                    "Please review eligibility criteria carefully as you might need additional documentation."
                )
            
            return analysis
            
        except Exception as e:
            print(f"Error in comprehensive analysis: {str(e)}")
            return None

    def analyze_context(self, scheme_info: SchemeInfo, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scheme in user's context."""
        try:
            context = {}
            
            # Analyze location relevance
            user_state = user_profile.get('state', '').lower()
            scheme_text = ' '.join([
                scheme_info.description.lower(),
                ' '.join(str(v).lower() for v in scheme_info.eligibility_criteria.values())
            ])
            
            if user_state in scheme_text:
                context['location_relevance'] = "This scheme is specifically available in your state."
            elif any(state in scheme_text for state in ['all states', 'any state', 'nationwide']):
                context['location_relevance'] = "This is a nationwide scheme."
            else:
                context['location_relevance'] = "Please verify state-specific eligibility."
            
            # Analyze timing and deadlines
            deadline_indicators = ['deadline', 'last date', 'closing date', 'valid until']
            for indicator in deadline_indicators:
                if indicator in scheme_text:
                    # Try to extract date information
                    context['time_sensitivity'] = "This scheme has specific deadlines. Please check the latest dates."
                    break
            
            # Analyze special categories
            special_categories = {
                'women': ['women', 'female', 'girl'],
                'students': ['student', 'education', 'school', 'college'],
                'farmers': ['farmer', 'agriculture', 'farming'],
                'elderly': ['senior citizen', 'elderly', 'aged'],
                'disabled': ['disability', 'differently abled', 'handicapped'],
                'minorities': ['minority', 'religious minority']
            }
            
            user_matches = []
            for category, keywords in special_categories.items():
                if any(keyword in scheme_text for keyword in keywords):
                    if self._user_matches_category(user_profile, category):
                        user_matches.append(category)
            
            if user_matches:
                context['special_category_match'] = f"This scheme is particularly relevant for {', '.join(user_matches)}."
            
            return context
            
        except Exception as e:
            print(f"Error in context analysis: {str(e)}")
            return {}

    def analyze_implementation_requirements(self, scheme_info: SchemeInfo) -> Dict[str, Any]:
        """Analyze implementation requirements and challenges."""
        try:
            requirements = {
                'documentation_level': 'low',
                'process_complexity': 'simple',
                'verification_needs': [],
                'potential_challenges': []
            }
            
            # Assess documentation requirements
            doc_count = len(scheme_info.required_documents)
            if doc_count > 5:
                requirements['documentation_level'] = 'high'
            elif doc_count > 3:
                requirements['documentation_level'] = 'medium'
            
            # Assess process complexity
            process_text = scheme_info.application_process.lower()
            complexity_indicators = {
                'visit': 'in-person visit required',
                'interview': 'interview process',
                'verification': 'verification process',
                'multiple': 'multiple steps',
                'original': 'original documents needed'
            }
            
            for indicator, description in complexity_indicators.items():
                if indicator in process_text:
                    requirements['verification_needs'].append(description)
                    if len(requirements['verification_needs']) > 2:
                        requirements['process_complexity'] = 'complex'
                    elif len(requirements['verification_needs']) > 1:
                        requirements['process_complexity'] = 'moderate'
            
            # Identify potential challenges
            if 'original' in process_text:
                requirements['potential_challenges'].append("Need to arrange original documents")
            if 'visit' in process_text:
                requirements['potential_challenges'].append("Requires in-person visits")
            if 'interview' in process_text:
                requirements['potential_challenges'].append("Interview preparation needed")
            
            return requirements
            
        except Exception as e:
            print(f"Error in implementation analysis: {str(e)}")
            return {}

    def _user_matches_category(self, user_profile: Dict[str, Any], category: str) -> bool:
        """Check if user matches a special category."""
        if category == 'women':
            return user_profile.get('gender', '').lower() == 'female'
        elif category == 'students':
            return user_profile.get('occupation', '').lower() == 'student'
        elif category == 'farmers':
            return user_profile.get('occupation', '').lower() == 'farmer'
        elif category == 'elderly':
            return user_profile.get('age', 0) >= 60
        elif category == 'minorities':
            return user_profile.get('category', '').lower() in ['minority', 'religious minority']
        return False

    def generate_user_friendly_output(
        self,
        scheme_info: SchemeInfo,
        user_profile: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> UserFriendlyAnalysis:
        """Generate user-friendly output from analysis results."""
        try:
            output = UserFriendlyAnalysis(scheme_info.scheme_name)
            
            # Add basic information
            output.summary = analysis_results.get('summary', '')
            output.key_benefits = scheme_info.benefits[:5]
            
            # Add eligibility information
            eligibility_results = analysis_results.get('eligibility_results', {})
            if eligibility_results:
                eligible_count = sum(1 for v in eligibility_results.values() if v)
                total_criteria = len(eligibility_results)
                if total_criteria > 0:
                    eligibility_percentage = (eligible_count / total_criteria * 100)
                    if eligibility_percentage >= 80:
                        output.eligibility_status = "You appear to be eligible for this scheme."
                    elif eligibility_percentage >= 50:
                        output.eligibility_status = "You partially meet the eligibility criteria."
                    else:
                        output.eligibility_status = "You might need to review your eligibility."
            
            # Add detailed eligibility results
            output.eligibility_details = eligibility_results
            
            # Add application process
            output.application_process = scheme_info.application_process
            
            # Add next steps
            implementation_reqs = analysis_results.get('implementation_requirements', {})
            next_steps = []
            if implementation_reqs.get('documentation_level') == 'high':
                next_steps.append("Start gathering all required documents early")
            if 'visit' in implementation_reqs.get('verification_needs', []):
                next_steps.append("Plan your visit to the relevant office")
            next_steps.extend([
                "Review all eligibility criteria thoroughly",
                "Prepare all necessary documents",
                "Submit your application",
                "Keep track of your application status"
            ])
            output.next_steps = next_steps
            
            # Add required documents
            output.required_documents = scheme_info.required_documents
            
            # Add success factors
            output.success_factors = [
                "Keep all documents ready before starting",
                "Double-check all information",
                "Submit application well before deadlines",
                "Keep copies of all submitted documents"
            ]
            
            # Add warnings
            output.warnings = []
            if implementation_reqs.get('process_complexity') == 'complex':
                output.warnings.append("This scheme has a complex application process")
            if implementation_reqs.get('documentation_level') == 'high':
                output.warnings.append("Multiple documents are required")
            output.warnings.extend(scheme_info.warnings)
            
            return output
            
        except Exception as e:
            print(f"Error generating user-friendly output: {str(e)}")
            return None