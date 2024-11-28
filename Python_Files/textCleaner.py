import re
import os

def clean_text_comprehensive(text):
    """
    Comprehensive text cleaning function that removes unwanted content,
    normalizes formatting, and prepares text for processing.
    Args:
        text (str): The raw text to be cleaned.
    Returns:
        str: The cleaned text.
    """

    # 1. Remove unwanted HTML tags or scripts
    text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL)  # Remove <script>...</script>
    text = re.sub(r"<.*?>", "", text)  # Remove any remaining HTML tags

    # 2. Remove unwanted metadata
    text = re.sub(r"\(adsbygoogle.*?\)", "", text)  # Remove Google ad placeholders
    text = re.sub(r"Content Source.*$", "", text, flags=re.MULTILINE)  # Remove content source links
    text = re.sub(r"SAVE AS PDF.*$", "", text, flags=re.MULTILINE)  # Remove SAVE AS PDF lines
    text = re.sub(r"Download Link.*$", "", text, flags=re.MULTILINE)  # Remove download links

    # 3. Remove URLs
    text = re.sub(r"http[s]?://\S+", "", text)  # Remove http/https URLs
    text = re.sub(r"www\.\S+", "", text)  # Remove www URLs

    # 4. Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()  # Replace multiple spaces/newlines with single space

    # 5. Replace non-ASCII characters
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII characters (or replace with spaces)

    # 6. Fix broken sentences
    text = re.sub(r"(?<=[a-zA-Z])\.\s(?=[A-Z])", ".\n", text)  # Add newlines after proper sentences

    # 7. Remove special characters or unwanted punctuation
    text = re.sub(r"[^\w\s.,:;!?'\"]+", "", text)  # Remove unnecessary symbols but keep basic punctuation

    # 8. Standardize case (optional)
    text = text.strip()  # Remove leading/trailing whitespace

    return text

def clean_file(file_path):
    """
    Cleans the text in a file and returns the cleaned content.
    Args:
        file_path (str): Path to the text file.
    Returns:
        str: Cleaned text content.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
        cleaned_text = clean_text_comprehensive(raw_text)
        return cleaned_text

def save_cleaned_text(cleaned_text, output_path):
    """
    Saves cleaned text to a file.
    Args:
        cleaned_text (str): Cleaned text content.
        output_path (str): Path to save the cleaned text file.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

def process_folder(folder_path):
    """
    Recursively processes all .txt files in a folder, cleans them, and saves in state-specific cleaned folders.
    Args:
        folder_path (str): Path to the folder containing raw text files.
    """
    # Get the state name from the folder path
    state_name = os.path.basename(folder_path).lower()
    
    # Create cleaned folder path
    parent_dir = os.path.dirname(folder_path)
    cleaned_folder = os.path.join(parent_dir, f"{state_name}-cleaned")
    
    print(f"\nProcessing files for state: {state_name}")
    print(f"Output directory: {cleaned_folder}")
    print("="*50)

    # Create the cleaned folder if it doesn't exist
    if not os.path.exists(cleaned_folder):
        os.makedirs(cleaned_folder)

    # Process each file
    files_processed = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                # Get the relative path from the input folder
                rel_path = os.path.relpath(root, folder_path)
                
                # Construct input and output paths
                input_path = os.path.join(root, file)
                output_path = os.path.join(cleaned_folder, rel_path, file)
                
                try:
                    # Clean the file
                    cleaned_text = clean_file(input_path)
                    
                    # Save the cleaned file
                    save_cleaned_text(cleaned_text, output_path)
                    
                    files_processed += 1
                    print(f"✓ Processed: {file}")
                    
                except Exception as e:
                    print(f"❌ Error processing {file}: {str(e)}")

    print("\nProcessing Summary:")
    print(f"Total files processed: {files_processed}")
    print(f"Cleaned files saved to: {cleaned_folder}")

# Example usage
if __name__ == "__main__":
    # Specify folder containing raw text files
    state_folder = "/Users/adityabhaskara/Downloads/Indian Government Schemes"
    
    # Process all files in the folder
    process_folder(state_folder)