import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pinecone_connection():
    try:
        # Print environment variables (with API key partially hidden)
        api_key = os.getenv('PINECONE_API_KEY')
        env = os.getenv('PINECONE_ENV')
        index_name = os.getenv('PINECONE_INDEX_NAME')
        
        print(f"API Key (first 10 chars): {api_key[:10]}...")
        print(f"Environment: {env}")
        print(f"Index Name: {index_name}")
        
        # Initialize Pinecone
        print("\nInitializing Pinecone...")
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        print("\nListing available indexes...")
        indexes = pc.list_indexes()
        print(f"Available indexes: {indexes.names()}")
        
        # Try to connect to index
        print(f"\nConnecting to index '{index_name}'...")
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"\nIndex stats: {stats}")
        
        print("\nPinecone connection test successful!")
        return True
        
    except Exception as e:
        print(f"\nError testing Pinecone connection: {str(e)}")
        return False

if __name__ == "__main__":
    test_pinecone_connection() 