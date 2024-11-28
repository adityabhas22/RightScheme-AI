import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import os
import time

# Load environment variables and initialize OpenAI client
load_dotenv()
client = OpenAI()

def read_chunks_from_files(chunks_dir):
    """Read all chunks from text files in the directory."""
    chunks_data = []
    chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.txt')]
    
    print(f"\nFound {len(chunk_files)} chunk files")
    
    for file_name in tqdm(chunk_files, desc="Reading files"):
        file_path = os.path.join(chunks_dir, file_name)
        current_chunk = []
        chunk_number = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            for line in lines:
                if line.strip().startswith('CHUNK'):
                    if current_chunk:
                        chunks_data.append({
                            "chunk_id": f"{file_name}_{chunk_number}",
                            "source_file": file_name,
                            "chunk_index": chunk_number,
                            "text": ' '.join(current_chunk)
                        })
                        current_chunk = []
                        chunk_number += 1
                elif not line.startswith('='):
                    current_chunk.append(line.strip())
            
            # Add the last chunk
            if current_chunk:
                chunks_data.append({
                    "chunk_id": f"{file_name}_{chunk_number}",
                    "source_file": file_name,
                    "chunk_index": chunk_number,
                    "text": ' '.join(current_chunk)
                })
    
    print(f"Total chunks extracted: {len(chunks_data)}")
    return chunks_data

def generate_embeddings_batch(texts, model="text-embedding-ada-002", batch_size=100):
    """Generate embeddings for a batch of texts."""
    all_embeddings = []
    
    # Process in batches
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
        batch = texts[i:i + batch_size]
        try:
            response = client.embeddings.create(
                input=batch,
                model=model
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"Error in batch {i//batch_size}: {str(e)}")
            return None
    
    return all_embeddings

def main():
    # Specify directories
    chunks_dir = "/Users/adityabhaskara/Downloads/chunks"  # Directory containing your chunk files
    output_dir = "/Users/adityabhaskara/Downloads/embeddings"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("Starting embedding generation process...")
    
    try:
        # Read chunks
        chunks_data = read_chunks_from_files(chunks_dir)
        if not chunks_data:
            print("No chunks found!")
            return
        
        # Prepare texts for embedding
        texts = [chunk['text'] for chunk in chunks_data]
        
        # Generate embeddings
        embeddings = generate_embeddings_batch(texts, batch_size=100)
        if embeddings is None:
            return
            
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save embeddings
        embeddings_file = os.path.join(output_dir, f"embeddings_{timestamp}.npy")
        np.save(embeddings_file, np.array(embeddings))
        
        # Save metadata
        metadata_file = os.path.join(output_dir, f"metadata_{timestamp}.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2)
        
        print("\nProcess completed successfully!")
        print(f"Embeddings saved to: {embeddings_file}")
        print(f"Metadata saved to: {metadata_file}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 