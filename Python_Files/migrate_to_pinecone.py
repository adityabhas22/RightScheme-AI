import faiss
import numpy as np
import json
import os
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_latest_faiss(vector_db_dir):
    """Load the most recent FAISS index and metadata."""
    try:
        # Use absolute path
        vector_db_dir = os.path.expanduser(vector_db_dir)
        
        print(f"Looking for FAISS files in: {vector_db_dir}")
        
        # Find most recent index file
        index_files = [f for f in os.listdir(vector_db_dir) if f.startswith('faiss_index_') and f.endswith('.index')]
        if not index_files:
            raise FileNotFoundError(f"No FAISS index files found in {vector_db_dir}")
        
        latest_index = max(index_files)
        index_path = os.path.join(vector_db_dir, latest_index)
        
        # Find corresponding metadata
        timestamp = latest_index.replace('faiss_index_', '').replace('.index', '')
        metadata_file = f'faiss_metadata_{timestamp}.json'
        metadata_path = os.path.join(vector_db_dir, metadata_file)
        
        print(f"Loading FAISS index from: {index_path}")
        print(f"Loading metadata from: {metadata_path}")
        
        # Load files
        index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        return index, metadata
    
    except Exception as e:
        print(f"Error loading FAISS index: {str(e)}")
        return None, None

def init_pinecone():
    """Initialize Pinecone client and create index if needed."""
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        index_name = os.getenv('PINECONE_INDEX_NAME')
        
        # Create index if it doesn't exist
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=1536,  # dimension for text-embedding-ada-002
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=os.getenv('PINECONE_ENV')
                )
            )
            print(f"Created new Pinecone index: {index_name}")
        
        return pc.Index(index_name)
    
    except Exception as e:
        print(f"Error initializing Pinecone: {str(e)}")
        return None

def migrate_to_pinecone(faiss_index, metadata, pinecone_index):
    """Migrate vectors from FAISS to Pinecone."""
    try:
        batch_size = 50  # Reduced batch size
        total = faiss_index.ntotal
        
        print(f"\nMigrating {total} vectors from FAISS to Pinecone...")
        print(f"Vector dimension: {faiss_index.d}")
        
        for i in range(0, total, batch_size):
            try:
                # Get batch of vectors from FAISS
                end_idx = min(i + batch_size, total)
                batch_ids = [str(j) for j in range(i, end_idx)]
                
                # Extract vectors from FAISS
                batch_vectors = []
                for j in range(i, end_idx):
                    vector = faiss.vector_to_array(faiss_index.reconstruct(int(j)))
                    batch_vectors.append(vector.tolist())
                
                # Get corresponding metadata
                batch_metadata = metadata[i:end_idx]
                
                # Create vectors for Pinecone
                vectors = []
                for id_, vector, meta in zip(batch_ids, batch_vectors, batch_metadata):
                    vectors.append({
                        'id': id_,
                        'values': vector,
                        'metadata': meta
                    })
                
                # Upsert to Pinecone
                pinecone_index.upsert(vectors=vectors)
                
                print(f"Migrated vectors {i} to {end_idx} of {total}")
                
            except Exception as batch_error:
                print(f"Error processing batch {i} to {end_idx}: {str(batch_error)}")
                continue
        
        print(f"\nSuccessfully migrated {total} vectors to Pinecone!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration(faiss_index, pinecone_index, num_samples=5):
    """Verify that vectors were correctly migrated."""
    try:
        print("\nVerifying migration...")
        
        total = faiss_index.ntotal
        test_indices = np.random.choice(total, num_samples, replace=False)
        
        for idx in test_indices:
            # Get vector from FAISS
            faiss_vector = faiss.vector_to_array(faiss_index.reconstruct(int(idx)))
            
            # Query Pinecone
            query_response = pinecone_index.query(
                vector=faiss_vector.tolist(),
                top_k=1,
                include_metadata=True
            )
            
            print(f"\nVector {idx}:")
            if query_response.matches:
                print(f"Found matching vector in Pinecone with score: {query_response.matches[0].score:.4f}")
            else:
                print("No matching vector found in Pinecone")
            
        print("\nVerification complete!")
        
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    # Use the full path to your vectorDb directory
    vector_db_dir = "/Users/adityabhaskara/Coding Projects/Jupyter Labs/Experimenting/Python_Files/vectorDb"
    
    print("Starting migration from FAISS to Pinecone...")
    
    # Load FAISS index and metadata
    faiss_index, metadata = load_latest_faiss(vector_db_dir)
    if faiss_index is None:
        return
        
    # Initialize Pinecone
    pinecone_index = init_pinecone()
    if pinecone_index is None:
        return
    
    # Perform migration
    success = migrate_to_pinecone(faiss_index, metadata, pinecone_index)
    if not success:
        return
    
    # Verify migration
    verify_migration(faiss_index, pinecone_index)
    
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    main() 