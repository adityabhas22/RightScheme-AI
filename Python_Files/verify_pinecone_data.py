import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_pinecone_data():
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))
        
        # Get index statistics
        stats = index.describe_index_stats()
        print("\nPinecone Index Statistics:")
        print(f"Total vector count: {stats.total_vector_count}")
        print(f"Dimension: {stats.dimension}")
        
        # Fetch a few random vectors
        if stats.total_vector_count > 0:
            print("\nFetching sample vectors...")
            # Query with a dummy vector of correct dimension
            dummy_vector = [0.0] * stats.dimension
            results = index.query(
                vector=dummy_vector,
                top_k=5,
                include_metadata=True
            )
            
            print("\nSample Results:")
            for i, match in enumerate(results.matches, 1):
                print(f"\nMatch {i}:")
                print(f"ID: {match.id}")
                print(f"Score: {match.score}")
                print("Metadata:", match.metadata.get('source_file', 'No source file'))
        
        return True
    
    except Exception as e:
        print(f"Error verifying Pinecone data: {str(e)}")
        return False

if __name__ == "__main__":
    verify_pinecone_data() 