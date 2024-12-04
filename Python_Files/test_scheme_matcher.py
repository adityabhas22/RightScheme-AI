#!/usr/bin/env python3
import unittest
import sys
import os
from typing import Dict, List
import logging

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from Python_Files.scheme_semantic_matcher import UserProfile, SemanticSchemeMatcher
from Python_Files.scheme_analyzer import SchemeAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all tests with detailed output."""
    # Create a test suite
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create a test runner with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(suite)
    
    # Return 0 if tests passed, 1 if any failed
    return 0 if result.wasSuccessful() else 1

class TestUserProfiles:
    """Collection of test user profiles"""
    
    @staticmethod
    def student_profile() -> Dict:
        return {
            'age': 21,
            'gender': 'Female',
            'category': 'SC',
            'annual_income': 150000,
            'occupation_category': 'Student',
            'education_level': 'Graduate',
            'institution_type': 'Government',
            'specific_requirement': ['scholarship', 'education loan'],
            'disability_status': 'No'
        }
    
    @staticmethod
    def farmer_profile() -> Dict:
        return {
            'age': 45,
            'gender': 'Male',
            'category': 'OBC',
            'annual_income': 300000,
            'occupation_category': 'Farmer/Agricultural Worker',
            'land_holding': '2-5 acres',
            'farming_type': 'Traditional',
            'specific_requirement': ['farming subsidies', 'equipment support'],
            'disability_status': 'No'
        }
    
    @staticmethod
    def senior_citizen_profile() -> Dict:
        return {
            'age': 65,
            'gender': 'Male',
            'category': 'General',
            'annual_income': 120000,
            'occupation_category': 'Senior Citizen',
            'living_status': 'With Family',
            'specific_requirement': ['pension', 'healthcare'],
            'disability_status': 'Yes',
            'disability_type': ['mobility']
        }
    
    @staticmethod
    def edge_case_profiles() -> List[Dict]:
        return [
            # Minimum age student
            {
                'age': 16,
                'gender': 'Male',
                'category': 'General',
                'annual_income': 0,
                'occupation_category': 'Student',
                'education_level': 'School (11-12)',
                'specific_requirement': ['scholarship'],
                'disability_status': 'No'
            },
            # Maximum income case
            {
                'age': 35,
                'gender': 'Female',
                'category': 'General',
                'annual_income': 1500000,
                'occupation_category': 'Employed',
                'employment_sector': 'Private',
                'specific_requirement': ['skill development'],
                'disability_status': 'No'
            },
            # Multiple disabilities
            {
                'age': 28,
                'gender': 'Male',
                'category': 'ST',
                'annual_income': 100000,
                'occupation_category': 'Unemployed',
                'education_level': 'Graduate',
                'specific_requirement': ['employment', 'disability support'],
                'disability_status': 'Yes',
                'disability_type': ['visual', 'hearing']
            }
        ]

class TestSchemeMatcher(unittest.TestCase):
    """Test cases for scheme matching system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        try:
            cls.matcher = SemanticSchemeMatcher()
            cls.analyzer = SchemeAnalyzer()
            cls.test_profiles = TestUserProfiles()
            logger.info("Test environment setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to set up test environment: {str(e)}")
            raise
    
    def setUp(self):
        """Set up before each test"""
        logger.info(f"Starting test: {self._testMethodName}")
    
    def tearDown(self):
        """Clean up after each test"""
        logger.info(f"Completed test: {self._testMethodName}")
    
    def test_student_schemes(self):
        """Test scheme matching for student profile"""
        logger.info("Testing student profile scheme matching...")
        profile_data = self.test_profiles.student_profile()
        state = "Karnataka"
        
        try:
            # Create UserProfile instance
            user_profile = UserProfile(
                age=profile_data['age'],
                gender=profile_data['gender'],
                category=profile_data['category'],
                annual_income=float(profile_data['annual_income']),
                occupation=profile_data['occupation_category'],
                occupation_details={'education_level': profile_data['education_level']},
                state=state,
                education_level=profile_data['education_level'],
                specific_needs=profile_data.get('specific_requirement', []),
                interests=", ".join(profile_data.get('specific_requirement', [])),
            )
            
            # Get recommendations
            recommendations = self.matcher.get_scheme_recommendations(user_profile)
            
            # Assertions
            self.assertIsNotNone(recommendations, "Recommendations should not be None")
            self.assertGreater(len(recommendations), 0, "Should have at least one recommendation")
            
            # Check if recommendations are relevant to students
            student_keywords = ['education', 'scholarship', 'student', 'academic']
            found_relevant = False
            for rec in recommendations:
                if any(keyword in rec.scheme_name.lower() for keyword in student_keywords):
                    found_relevant = True
                    break
            self.assertTrue(found_relevant, "No student-relevant schemes found")
            
            logger.info("Student scheme test completed successfully")
            
        except Exception as e:
            logger.error(f"Student scheme test failed: {str(e)}")
            raise
    
    def test_farmer_schemes(self):
        """Test scheme matching for farmer profile"""
        logger.info("Testing farmer profile scheme matching...")
        profile_data = self.test_profiles.farmer_profile()
        state = "Karnataka"
        
        try:
            user_profile = UserProfile(
                age=profile_data['age'],
                gender=profile_data['gender'],
                category=profile_data['category'],
                annual_income=float(profile_data['annual_income']),
                occupation=profile_data['occupation_category'],
                occupation_details={
                    'land_holding': profile_data['land_holding'],
                    'farming_type': profile_data['farming_type']
                },
                state=state,
                education_level='',
                specific_needs=profile_data.get('specific_requirement', []),
                interests=", ".join(profile_data.get('specific_requirement', [])),
            )
            
            recommendations = self.matcher.get_scheme_recommendations(user_profile)
            
            self.assertIsNotNone(recommendations, "Recommendations should not be None")
            self.assertGreater(len(recommendations), 0, "Should have at least one recommendation")
            
            # Check for farmer-relevant schemes
            farmer_keywords = ['farm', 'agriculture', 'kisan', 'crop']
            found_relevant = False
            for rec in recommendations:
                if any(keyword in rec.scheme_name.lower() for keyword in farmer_keywords):
                    found_relevant = True
                    break
            self.assertTrue(found_relevant, "No farmer-relevant schemes found")
            
            logger.info("Farmer scheme test completed successfully")
            
        except Exception as e:
            logger.error(f"Farmer scheme test failed: {str(e)}")
            raise
    
    def test_edge_cases(self):
        """Test scheme matching for edge cases"""
        logger.info("Testing edge case profiles...")
        state = "Karnataka"
        
        for i, profile_data in enumerate(self.test_profiles.edge_case_profiles()):
            try:
                logger.info(f"Testing edge case profile {i + 1}")
                user_profile = UserProfile(
                    age=profile_data['age'],
                    gender=profile_data['gender'],
                    category=profile_data['category'],
                    annual_income=float(profile_data['annual_income']),
                    occupation=profile_data['occupation_category'],
                    occupation_details={},
                    state=state,
                    education_level=profile_data.get('education_level', ''),
                    specific_needs=profile_data.get('specific_requirement', []),
                    interests=", ".join(profile_data.get('specific_requirement', [])),
                )
                
                recommendations = self.matcher.get_scheme_recommendations(user_profile)
                
                # Basic validation
                self.assertIsNotNone(recommendations, f"Recommendations for edge case {i + 1} should not be None")
                
                # Specific edge case validations
                if profile_data['annual_income'] > 1000000:
                    # High income case should still return some schemes
                    self.assertLess(len(recommendations), 10, 
                                  "Too many schemes for high income profile")
                
                if profile_data.get('disability_status') == 'Yes':
                    # Should find disability-related schemes
                    disability_keywords = ['disability', 'divyang', 'handicap']
                    found_disability_scheme = False
                    for rec in recommendations:
                        if any(keyword in rec.scheme_name.lower() 
                              for keyword in disability_keywords):
                            found_disability_scheme = True
                            break
                    self.assertTrue(found_disability_scheme, 
                                  "No disability schemes found for disabled profile")
                
                logger.info(f"Edge case profile {i + 1} tested successfully")
                
            except Exception as e:
                logger.error(f"Edge case {i + 1} test failed: {str(e)}")
                raise
    
    def test_eligibility_checking(self):
        """Test eligibility checking functionality"""
        logger.info("Testing eligibility checking...")
        profile_data = self.test_profiles.student_profile()
        state = "Karnataka"
        
        try:
            user_profile = UserProfile(
                age=profile_data['age'],
                gender=profile_data['gender'],
                category=profile_data['category'],
                annual_income=float(profile_data['annual_income']),
                occupation=profile_data['occupation_category'],
                occupation_details={'education_level': profile_data['education_level']},
                state=state,
                education_level=profile_data['education_level'],
                specific_needs=profile_data.get('specific_requirement', []),
                interests=", ".join(profile_data.get('specific_requirement', [])),
            )
            
            recommendations = self.matcher.get_scheme_recommendations(user_profile)
            
            for rec in recommendations:
                # Check if eligibility status is properly set
                self.assertIn('eligibility_status', rec.dict(), 
                            "Recommendation should have eligibility_status")
                self.assertIsInstance(rec.eligibility_status, dict, 
                                    "eligibility_status should be a dictionary")
                
                # Verify eligibility requirements
                self.assertTrue(len(rec.eligibility_requirements) > 0, 
                              "Should have eligibility requirements")
                
                # Check if benefits are provided
                self.assertTrue(len(rec.benefits) > 0, 
                              "Should have benefits listed")
                
                # Verify relevance score is within bounds
                self.assertGreaterEqual(rec.relevance_score, 0.0, 
                                      "Relevance score should be >= 0")
                self.assertLessEqual(rec.relevance_score, 1.0, 
                                   "Relevance score should be <= 1")
            
            logger.info("Eligibility checking test completed successfully")
            
        except Exception as e:
            logger.error(f"Eligibility checking test failed: {str(e)}")
            raise

if __name__ == '__main__':
    sys.exit(run_tests()) 