import faiss
import numpy as np
import json
import os
from datetime import datetime

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

def create_faiss_index(embeddings, index_type="l2"):
    """Create and populate a FAISS index."""
    try:
        vector_dimension = embeddings.shape[1]
        
        # Choose index type
        if index_type == "l2":
            index = faiss.IndexFlatL2(vector_dimension)
        elif index_type == "ip":  # Inner product
            index = faiss.IndexFlatIP(vector_dimension)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")
        
        # Add vectors to the index
        index.add(embeddings)
        
        print(f"\nCreated FAISS index:")
        print(f"- Type: {index_type}")
        print(f"- Dimension: {vector_dimension}")
        print(f"- Number of vectors: {index.ntotal}")
        
        return index
    
    except Exception as e:
        print(f"Error creating FAISS index: {str(e)}")
        return None

def save_faiss_index(index, metadata, output_dir):
    """Save the FAISS index and metadata."""
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save FAISS index
        index_path = os.path.join(output_dir, f"faiss_index_{timestamp}.index")
        faiss.write_index(index, index_path)
        
        # Save metadata
        metadata_path = os.path.join(output_dir, f"faiss_metadata_{timestamp}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved FAISS index to: {index_path}")
        print(f"Saved metadata to: {metadata_path}")
        
        return index_path, metadata_path
    
    except Exception as e:
        print(f"Error saving FAISS index: {str(e)}")
        return None, None

def test_faiss_index(index, metadata, num_queries=3, top_k=5):
    """Test the FAISS index with random queries."""
    try:
        print("\nTesting FAISS index...")
        
        # Get random vectors for testing
        num_vectors = index.ntotal
        test_indices = np.random.choice(num_vectors, num_queries, replace=False)
        
        for i, idx in enumerate(test_indices):
            print(f"\nTest Query {i+1}:")
            
            # Get a vector and search
            query_vector = faiss.vector_to_array(index.reconstruct(int(idx)))
            distances, indices = index.search(query_vector.reshape(1, -1), top_k)
            
            print(f"Original document: {metadata[idx]['source_file']}")
            print(f"\nTop {top_k} matches:")
            
            for j, (dist, matched_idx) in enumerate(zip(distances[0], indices[0])):
                matched_doc = metadata[matched_idx]['source_file']
                print(f"{j+1}. Distance: {dist:.4f} - Document: {matched_doc}")
    
    except Exception as e:
        print(f"Error testing FAISS index: {str(e)}")

def main():
    # Specify directories
    embeddings_dir = "/Users/adityabhaskara/Downloads/embeddings"
    output_dir = "/Users/adityabhaskara/Downloads/vectorDb"
    
    print("Starting FAISS index creation...")
    
    # Load embeddings and metadata
    embeddings, metadata = load_embeddings_and_metadata(embeddings_dir)
    if embeddings is None or metadata is None:
        return
    
    # Create FAISS index
    index = create_faiss_index(embeddings, index_type="l2")
    if index is None:
        return
    
    # Save the index and metadata
    index_path, metadata_path = save_faiss_index(index, metadata, output_dir)
    if index_path is None:
        return
    
    # Test the index
    test_faiss_index(index, metadata)
    
    print("\nFAISS index creation completed successfully!")

if __name__ == "__main__":
    main()