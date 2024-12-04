#!/usr/bin/env python3
"""Test script for the scheme matching pipeline."""

import os
import sys
import json
from typing import List
from dotenv import load_dotenv
from Python_Files.scheme_matcher import SchemeMatcher, UserProfile, SchemeCategory

# Load environment variables
load_dotenv()

def test_scheme_matcher() -> None:
    """Test the scheme matching pipeline."""
    try:
        # Initialize matcher
        print("Initializing SchemeMatcher...")
        matcher = SchemeMatcher()
        
        # Create test user profile
        print("\nCreating test user profile...")
        test_profile = UserProfile(
            age=25,
            gender="Male",
            category="General",
            annual_income=300000,
            occupation="Farmer",
            state="Karnataka",
            education_level="Graduate",
            specific_needs=["Agriculture Support", "Financial Support"]
        )
        print(f"Test profile created: {test_profile}")
        
        # Get matching schemes
        print("\nSearching for matching schemes...")
        matches = matcher.get_matching_schemes(test_profile)
        
        # Print results
        print(f"\nFound {len(matches)} matching schemes:")
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match.scheme_name}")
            print(f"   Category: {match.category.value}")
            print(f"   Relevance Score: {match.relevance_score:.2f}")
            print(f"   Priority Level: {match.priority_level}")
            print("   Eligibility:")
            for criterion, matches in match.eligibility_match.items():
                print(f"      {criterion}: {'✓' if matches else '✗'}")
            print("   Benefits:")
            for benefit in match.benefits:
                print(f"      • {benefit}")
            if match.application_process:
                print(f"   Application Process: {match.application_process}")
            print("-" * 80)
    except Exception as e:
        print(f"Error in test_scheme_matcher: {str(e)}")
        raise

def test_with_different_profiles() -> None:
    """Test scheme matcher with different user profiles."""
    try:
        matcher = SchemeMatcher()
        
        test_profiles = [
            UserProfile(
                age=25,
                gender="Male",
                category="General",
                annual_income=300000,
                occupation="Farmer",
                state="Karnataka",
                education_level="Graduate",
                specific_needs=["Agriculture Support"]
            ),
            UserProfile(
                age=35,
                gender="Female",
                category="SC",
                annual_income=200000,
                occupation="Self-employed",
                state="Karnataka",
                education_level="12th Pass",
                specific_needs=["Business Support"]
            ),
            UserProfile(
                age=20,
                gender="Female",
                category="General",
                annual_income=0,
                occupation="Student",
                state="Karnataka",
                education_level="12th Pass",
                specific_needs=["Education Support"]
            )
        ]
        
        for i, profile in enumerate(test_profiles, 1):
            try:
                print(f"\nTesting Profile {i}:")
                print(f"Age: {profile.age}")
                print(f"Gender: {profile.gender}")
                print(f"Category: {profile.category}")
                print(f"Occupation: {profile.occupation}")
                print(f"Specific Needs: {profile.specific_needs}")
                
                matches = matcher.get_matching_schemes(profile)
                print(f"\nFound {len(matches)} matching schemes:")
                
                # Print top 3 matches for each profile
                for j, match in enumerate(matches[:3], 1):
                    print(f"\n   {j}. {match.scheme_name}")
                    print(f"      Relevance Score: {match.relevance_score:.2f}")
                    print(f"      Category: {match.category.value}")
                    print("      Eligibility Match:", end=" ")
                    eligible = all(match.eligibility_match.values())
                    print("✓" if eligible else "✗")
                print("-" * 80)
            except Exception as e:
                print(f"Error testing profile {i}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error in test_with_different_profiles: {str(e)}")
        raise

def test_search_query_generation(matcher: SchemeMatcher, profile: UserProfile) -> None:
    """Test the search query generation."""
    try:
        print("\nTesting search query generation...")
        query = matcher._generate_search_query(profile)
        print(f"Generated query: {query}")
    except Exception as e:
        print(f"Error in test_search_query_generation: {str(e)}")
        raise

def test_embedding_generation(matcher: SchemeMatcher) -> None:
    """Test the embedding generation."""
    try:
        print("\nTesting embedding generation...")
        test_text = "Test query for agriculture schemes in Karnataka"
        embedding = matcher._get_embedding(test_text)
        print(f"Generated embedding length: {len(embedding)}")
        print(f"First few dimensions: {embedding[:5]}")
    except Exception as e:
        print(f"Error in test_embedding_generation: {str(e)}")
        raise

def main() -> None:
    """Run all tests."""
    print("Starting scheme matcher tests...\n")
    
    try:
        # Check environment variables
        required_vars = ['PINECONE_API_KEY', 'PINECONE_INDEX_NAME', 'OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
        
        print("=== Test 1: Basic Scheme Matching ===")
        test_scheme_matcher()
        
        print("\n=== Test 2: Multiple Profile Testing ===")
        test_with_different_profiles()
        
        # Create instances for additional tests
        matcher = SchemeMatcher()
        test_profile = UserProfile(
            age=25,
            gender="Male",
            category="General",
            annual_income=300000,
            occupation="Farmer",
            state="Karnataka",
            education_level="Graduate",
            specific_needs=["Agriculture Support"]
        )
        
        print("\n=== Test 3: Search Query Generation ===")
        test_search_query_generation(matcher, test_profile)
        
        print("\n=== Test 4: Embedding Generation ===")
        test_embedding_generation(matcher)
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 