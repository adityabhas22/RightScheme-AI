import numpy as np
import json
import os
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_pinecone():
    """Initialize Pinecone client and create index if it doesn't exist."""
    try:
        # Initialize Pinecone
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

def load_embeddings_and_metadata(embeddings_dir):
    """Load the most recent embeddings and metadata files."""
    try:
        # Find the most recent embeddings file
        embeddings_files = [f for f in os.listdir(embeddings_dir) if f.startswith('embeddings_') and f.endswith('.npy')]
        if not embeddings_files:
            raise FileNotFoundError("No embeddings files found")
        
        latest_embeddings = max(embeddings_files)
        embeddings_path = os.path.join(embeddings_dir, latest_embeddings)
        
        # Find corresponding metadata file
        timestamp = latest_embeddings.replace('embeddings_', '').replace('.npy', '')
        metadata_file = f'metadata_{timestamp}.json'
        metadata_path = os.path.join(embeddings_dir, metadata_file)
        
        print(f"Loading embeddings from: {embeddings_path}")
        print(f"Loading metadata from: {metadata_path}")
        
        # Load the files
        embeddings = np.load(embeddings_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        return embeddings, metadata
    
    except Exception as e:
        print(f"Error loading files: {str(e)}")
        return None, None

def upsert_to_pinecone(index, embeddings, metadata):
    """Upload vectors and metadata to Pinecone."""
    try:
        batch_size = 50
        total = len(metadata)
        
        for i in range(0, total, batch_size):
            # Prepare batch
            end_idx = min(i + batch_size, total)
            batch_ids = [str(j) for j in range(i, end_idx)]
            batch_embeddings = embeddings[i:end_idx].tolist()
            batch_metadata = metadata[i:end_idx]
            
            # Create vectors for Pinecone
            vectors = []
            for id_, vector, meta in zip(batch_ids, batch_embeddings, batch_metadata):
                vectors.append({
                    'id': id_,
                    'values': vector,
                    'metadata': meta
                })
            
            # Upsert to Pinecone
            index.upsert(vectors=vectors)
            
            print(f"Uploaded vectors {i} to {end_idx} of {total}")
        
        print(f"\nSuccessfully uploaded {total} vectors to Pinecone")
        return True
        
    except Exception as e:
        print(f"Error uploading to Pinecone: {str(e)}")
        return False

def main():
    # Specify directories
    embeddings_dir = "/Users/adityabhaskara/Downloads/embeddings"
    
    print("Starting Pinecone index creation...")
    
    # Initialize Pinecone
    index = init_pinecone()
    if index is None:
        return
    
    # Load embeddings and metadata
    embeddings, metadata = load_embeddings_and_metadata(embeddings_dir)
    if embeddings is None or metadata is None:
        return
    
    # Upload to Pinecone
    success = upsert_to_pinecone(index, embeddings, metadata)
    if not success:
        return
    
    print("\nPinecone index creation completed successfully!")

if __name__ == "__main__":
    main()