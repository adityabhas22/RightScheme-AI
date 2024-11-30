import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import os
import time
import json

# Load environment variables and initialize OpenAI client
load_dotenv()
client = OpenAI()

def find_chunk_files(chunks_dir):
    """Recursively find all chunk files in the directory structure."""
    chunk_files = []
    chunk_data = []
    
    print(f"\nScanning directory: {chunks_dir}")
    
    for root, _, files in os.walk(chunks_dir):
        for file in files:
            if file.endswith('.txt') and 'chunk' in file.lower():
                file_path = os.path.join(root, file)
                # Extract document name from parent directory
                doc_name = os.path.basename(os.path.dirname(file_path))
                chunk_number = int(file.split('_chunk_')[1].split('.')[0])
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read().strip()
                        
                    chunk_data.append({
                        "chunk_id": f"{doc_name}_chunk_{chunk_number:04d}",
                        "source_file": doc_name,
                        "chunk_index": chunk_number,
                        "text": text_content,
                        "file_path": file_path
                    })
                    chunk_files.append(file_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    print(f"Found {len(chunk_files)} chunk files")
    return chunk_data

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

def main(input_dir, output_dir):
    """Main function to process chunks and generate embeddings."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("Starting embedding generation process...")
    
    try:
        # Find and read all chunk files
        chunks_data = find_chunk_files(input_dir)
        if not chunks_data:
            print("No chunk files found!")
            return
        
        # Prepare texts for embedding
        texts = [chunk['text'] for chunk in chunks_data]
        
        # Generate embeddings
        print(f"\nGenerating embeddings for {len(texts)} chunks...")
        embeddings = generate_embeddings_batch(texts, batch_size=100)
        if embeddings is None:
            return
            
        # Save results with timestamp
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
        print(f"Total chunks processed: {len(chunks_data)}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Specify your directories
    input_dir = "/Users/adityabhaskara/Downloads/newchunks/new chunks"  # Directory containing your chunk files
    output_dir = "/Users/adityabhaskara/Downloads/newembeddings"  # Directory to save embeddings and metadata
    
    main(input_dir, output_dir) 