from transformers import GPT2TokenizerFast
import os
import re
from typing import List, Dict
import unicodedata
import json
from datetime import datetime
import time

class TextCleaner:
    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        """Remove extra whitespace, including multiple newlines."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*', '\n\n', text)
        return text.strip()

    @staticmethod
    def fix_unicode(text: str) -> str:
        """Fix unicode issues and normalize text."""
        return unicodedata.normalize('NFKC', text)

    @staticmethod
    def remove_special_characters(text: str) -> str:
        """Remove unwanted special characters but keep punctuation."""
        # Keep basic punctuation but remove other special characters
        return re.sub(r'[^\w\s.,!?;:()\-\'\"]+', ' ', text)

    @staticmethod
    def fix_common_issues(text: str) -> str:
        """Fix common text issues."""
        # Fix common abbreviations
        text = re.sub(r'(?<=\w)\.(?=\w)', '. ', text)
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
        # Fix multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        return text

    @staticmethod
    def clean_text(text: str) -> str:
        """Apply all cleaning operations."""
        text = TextCleaner.fix_unicode(text)
        text = TextCleaner.remove_special_characters(text)
        text = TextCleaner.fix_common_issues(text)
        text = TextCleaner.remove_extra_whitespace(text)
        return text

class TextChunker:
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        return len(self.tokenizer(text)["input_ids"])

    def create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks of text based on semantic boundaries."""
        chunks = []
        
        # First, split into paragraphs
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_tokens = 0
        last_overlap = ""
        
        for paragraph in paragraphs:
            # Clean and split paragraph into sentences
            sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                sentence_tokens = self.count_tokens(sentence)
                
                # If single sentence is too long, split it
                if sentence_tokens > self.max_tokens:
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                    words = sentence.split()
                    current_chunk = []
                    current_tokens = 0
                    temp_chunk = []
                    temp_tokens = 0
                    
                    for word in words:
                        word_tokens = self.count_tokens(word)
                        if temp_tokens + word_tokens <= self.max_tokens:
                            temp_chunk.append(word)
                            temp_tokens += word_tokens
                        else:
                            chunks.append(' '.join(temp_chunk))
                            temp_chunk = [word]
                            temp_tokens = word_tokens
                    
                    if temp_chunk:
                        current_chunk = temp_chunk
                        current_tokens = temp_tokens
                    continue
                
                # Check if adding this sentence would exceed the limit
                if current_tokens + sentence_tokens > self.max_tokens:
                    if current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        chunks.append(chunk_text)
                        
                        # Create overlap with last few sentences
                        overlap_text = ' '.join(current_chunk[-2:])  # Last 2 sentences
                        if self.count_tokens(overlap_text) <= self.overlap_tokens:
                            last_overlap = overlap_text
                        else:
                            last_overlap = current_chunk[-1]  # Just the last sentence
                        
                        current_chunk = []
                        if last_overlap:
                            current_chunk.extend(last_overlap.split())
                            current_tokens = self.count_tokens(last_overlap)
                        else:
                            current_tokens = 0
                
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

def save_chunks_to_json(chunks_by_file: Dict[str, List[str]], output_dir: str):
    """
    Save chunks in a structured JSON format suitable for embedding generation.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Prepare structured data for JSON
    chunks_data = []
    for filename, chunks in chunks_by_file.items():
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "chunk_id": f"{filename}_{i}",
                "source_file": filename,
                "chunk_index": i,
                "text": chunk,
                "token_count": TextChunker().count_tokens(chunk),
                "char_count": len(chunk),
                "word_count": len(chunk.split())
            }
            chunks_data.append(chunk_data)
    
    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"chunks_{timestamp}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nChunks saved to: {output_file}")
    print(f"Total chunks saved: {len(chunks_data)}")
    return output_file

def process_files_in_folder(folder_path: str, max_tokens: int = 512) -> Dict[str, List[str]]:
    """Process all text files in a folder with chunking."""
    chunker = TextChunker(max_tokens=max_tokens)
    chunks_by_file = {}
    
    print(f"\nProcessing files in {folder_path}")
    print("=" * 50)

    # First, verify the folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found at {folder_path}")
        return {}

    # Create chunks folder
    chunks_folder = os.path.join(os.path.dirname(folder_path), "chunks")
    if not os.path.exists(chunks_folder):
        os.makedirs(chunks_folder)

    files_processed = 0
    total_chunks = 0

    for root, _, files in os.walk(folder_path):
        txt_files = [f for f in files if f.endswith('.txt')]
        if not txt_files:
            print(f"No .txt files found in {folder_path}")
            continue

        print(f"\nFound {len(txt_files)} text files to process")
        
        for file in txt_files:
            file_path = os.path.join(root, file)
            try:
                print(f"\nProcessing: {file}")
                
                # Read the file
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                print(f"- Read {len(text)} characters")
                
                # Generate chunks
                chunks = chunker.create_chunks(text)
                print(f"- Generated {len(chunks)} initial chunks")
                
                # Verify chunks
                valid_chunks = []
                for i, chunk in enumerate(chunks):
                    tokens = chunker.count_tokens(chunk)
                    if tokens <= max_tokens:
                        valid_chunks.append(chunk)
                    else:
                        print(f"  Warning: Chunk {i+1} exceeded token limit ({tokens} tokens)")
                
                # Save chunks to file
                chunk_file = os.path.join(chunks_folder, f"{file.replace('.txt', '')}_chunks.txt")
                with open(chunk_file, "w", encoding="utf-8") as f:
                    for i, chunk in enumerate(valid_chunks, 1):
                        f.write(f"CHUNK {i}\n")
                        f.write("="*50 + "\n")
                        f.write(chunk + "\n\n")
                
                chunks_by_file[file] = valid_chunks
                files_processed += 1
                total_chunks += len(valid_chunks)
                
                print(f"✓ Created {len(valid_chunks)} valid chunks")
                print(f"✓ Saved chunks to: {chunk_file}")
                
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")
                continue

    print("\nProcessing Summary:")
    print(f"Files processed: {files_processed}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Chunks saved to: {chunks_folder}")
    
    return chunks_by_file

def display_chunks(chunks_by_file: Dict[str, List[str]], num_files: int = 1, num_chunks: int = 3):
    """Display processed chunks with detailed information."""
    if not chunks_by_file:
        print("No chunks to display!")
        return

    print("\nChunk Analysis:")
    print("=" * 50)
    
    for i, (filename, chunks) in enumerate(chunks_by_file.items()):
        if i >= num_files:
            break
            
        print(f"\nFile: {filename}")
        print(f"Total chunks: {len(chunks)}")
        
        chunker = TextChunker()
        for j, chunk in enumerate(chunks[:num_chunks]):
            token_count = chunker.count_tokens(chunk)
            char_count = len(chunk)
            
            print(f"\nChunk {j + 1}:")
            print("-" * 40)
            print(chunk)
            print("-" * 40)
            print(f"Statistics:")
            print(f"- Tokens: {token_count}")
            print(f"- Characters: {char_count}")
            print(f"- Words: {len(chunk.split())}")

def process_existing_chunks(chunks_dir: str, output_dir: str):
    """
    Process existing chunked text files and convert them to JSON format.
    Args:
        chunks_dir: Directory containing the chunked text files
        output_dir: Directory to save the JSON output
    """
    chunks_by_file = {}
    
    print(f"\nProcessing existing chunks from: {chunks_dir}")
    print("=" * 50)
    
    try:
        # Get all text files in the chunks directory
        chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.txt')]
        
        if not chunk_files:
            print("No chunk files found!")
            return None
            
        print(f"Found {len(chunk_files)} chunk files")
        total_chunks = 0
        
        for file_name in chunk_files:
            file_path = os.path.join(chunks_dir, file_name)
            chunks = []
            current_chunk = []
            
            print(f"\nProcessing: {file_name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines:
                    if line.strip().startswith('CHUNK'):
                        if current_chunk:  # Save previous chunk if exists
                            chunks.append(' '.join(current_chunk))
                            current_chunk = []
                    elif not line.startswith('='):  # Skip separator lines
                        current_chunk.append(line.strip())
                
                # Add the last chunk if exists
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
            
            if chunks:  # Only add if we found chunks
                chunks_by_file[file_name] = chunks
                total_chunks += len(chunks)
                print(f"✓ Extracted {len(chunks)} chunks")
            
            # Add a small delay to prevent system overload
            time.sleep(0.1)
    
        if chunks_by_file:
            # Save to JSON
            json_file = save_chunks_to_json(chunks_by_file, output_dir)
            print(f"\nProcessed {len(chunk_files)} files")
            print(f"Total chunks extracted: {total_chunks}")
            print(f"All chunks saved to: {json_file}")
            return chunks_by_file
        else:
            print("No valid chunks found in any file.")
            return None
        
    except Exception as e:
        print(f"Error processing chunks: {str(e)}")
        return None

if __name__ == "__main__":
    # Specify your directories
    chunks_dir = "/Users/adityabhaskara/Downloads/chunks"  # Your source chunks directory
    output_dir = "/Users/adityabhaskara/Downloads"  # Where to save the JSON
    
    print("Starting chunk processing...")
    
    try:
        # Process existing chunks with timeout
        chunks_by_file = process_existing_chunks(chunks_dir, output_dir)
        
        if chunks_by_file:
            # Display sample analysis
            display_chunks(chunks_by_file, num_files=1, num_chunks=2)
            print("\nChunk processing completed successfully!")
        else:
            print("No chunks were processed. Please check the input directory.")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        print("\nProcessing finished.")

