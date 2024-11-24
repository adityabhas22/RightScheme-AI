import faiss
import numpy as np
import json
import openai
from dotenv import load_dotenv
import os

load_dotenv('.env.local')  # Explicitly specify .env.local file
openai.api_key = os.getenv("OPENAI_API_KEY")  # Retrieve the OpenAI API key from environment variables
if not openai.api_key:
    raise ValueError("OpenAI API key not found in .env.local file")


# Load precomputed embeddings and metadata
with open("/Users/adityabhaskara/Coding Projects/Jupyter Labs/Vector Database /embeddings.npy", "rb") as f:
    scheme_vectors = np.load(f)

with open("/Users/adityabhaskara/Coding Projects/Jupyter Labs/Vector Database /metadata.json", "r") as f:
    metadata = json.load(f)

# Load scheme details linked by ID
with open("/Users/adityabhaskara/Coding Projects/Jupyter Labs/Vector Database /scheme_details.json", "r") as f:
    scheme_details = json.load(f)

# Load FAISS Index
dimension = scheme_vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(scheme_vectors)

# After loading the data, add these checks
print(f"Number of vectors in FAISS: {index.ntotal}")
print(f"Number of entries in metadata: {len(metadata)}")
print(f"Number of entries in scheme_details: {len(scheme_details)}")

# Function to embed user query
def embed_text(text):
    """Generate embedding for a given text."""
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return np.array(response['data'][0]['embedding'], dtype='float32')

def format_eligibility(eligibility_list):
    """
    Format eligibility criteria into human-readable text.
    """
    formatted_eligibility = []
    
    for item in eligibility_list:
        if isinstance(item, dict):
            name = item.get('name', '').replace('_', ' ').title()
            value = item.get('value', '')
            
            # Format based on different criteria types
            if name == 'Income Limit':
                formatted = f"Annual income should be less than ₹{value:,}"
            elif name == 'State':
                formatted = f"Must be a resident of {value}"
            elif name == 'Caste':
                formatted = f"Belongs to {value} category"
            elif name == 'Employment Status':
                formatted = f"Employment Status: {value}"
            elif name == 'Age':
                formatted = f"Age should be {value} years"
            else:
                formatted = f"{name}: {value}"
                
            formatted_eligibility.append(formatted)
        else:
            # Handle cases where eligibility is a simple string
            formatted_eligibility.append(str(item))
    
    return formatted_eligibility

# Function to query the database and retrieve enriched results
def query_and_enrich_schemes(user_query, top_k=5):
    """
    Retrieve best matching schemes for a user query and provide enriched details.
    Args:
        user_query (str): The user's input query.
        top_k (int): Number of top matching schemes to return.
    Returns:
        List[dict]: Structured output for the matching schemes including eligibility.
    """
    try:
        query_vector = embed_text(user_query).reshape(1, -1)
        
        # Query FAISS index
        distances, indices = index.search(query_vector, top_k)
        
        # Print debug information
        print(f"Found {len(indices[0])} matches")
        print(f"Indices shape: {indices.shape}")
        print(f"Distances shape: {distances.shape}")
        
        # Retrieve and enrich matching schemes
        matching_schemes = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # Valid match
                scheme_id = metadata[idx]["id"]
                # Retrieve detailed scheme information
                scheme_detail = next((d for d in scheme_details if d["scheme_id"] == scheme_id), {})
                if scheme_detail:
                    # Format eligibility before adding to results
                    raw_eligibility = scheme_detail.get("eligibility", [])
                    formatted_eligibility = format_eligibility(raw_eligibility)
                    
                    matching_schemes.append({
                        "scheme_id": scheme_id,
                        "scheme_name": scheme_detail.get("scheme_name", "Unnamed Scheme"),
                        "benefits": scheme_detail.get("benefits", []),
                        "application_process": scheme_detail.get("application_process", []),
                        "documents_required": scheme_detail.get("documents_required", []),
                        "eligibility": formatted_eligibility,
                        "distance_score": float(distances[0][i])
                    })
        
        return matching_schemes
    
    except Exception as e:
        print(f"Error in query_and_enrich_schemes: {str(e)}")
        return []

# Test different user scenarios
test_queries = [
    "I am a woman entrepreneur in Delhi looking to start a small business",
    "Looking for education scholarships for SC/ST students in Maharashtra",
    "I am a self-employed farmer in Karnataka looking for subsidies for seeds and fertilizers."
]

print("\n=== Testing Multiple User Queries ===\n")

for query in test_queries:
    print("\n" + "="*80)
    print(f"USER QUERY: {query}")
    print("="*80 + "\n")
    
    top_schemes = query_and_enrich_schemes(query, top_k=2)
    
    if not top_schemes:
        print("No matching schemes found.")
        continue
        
    for scheme in top_schemes:
        print(f"\nScheme ID: {scheme['scheme_id']}")
        print(f"Scheme Name: {scheme['scheme_name']}")
        
        print("\n📋 Eligibility Criteria:")
        for eligibility in scheme['eligibility']:
            print(f"  • {eligibility}")
        
        print("\n💰 Benefits:")
        for benefit in scheme['benefits']:
            print(f"  • {benefit}")
            
        print("\n📝 Application Process:")
        for step in scheme['application_process']:
            print(f"  • {step}")
            
        print("\n📄 Required Documents:")
        for doc in scheme['documents_required']:
            print(f"  • {doc}")
            
        print(f"\n📊 Relevance Score: {scheme['distance_score']:.4f}")
        print("-"*50)

# Add this at the end of your script if you want to save results to a file
import sys
from datetime import datetime

# Redirect stdout to a file
original_stdout = sys.stdout
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
with open(f'query_results_{timestamp}.txt', 'w') as f:
    sys.stdout = f
    # Run your queries here
    # ... (previous test code)
    sys.stdout = original_stdout
