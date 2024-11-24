# Vector Database Search Instructions

This guide explains how to use the searchDb.py script to search through government schemes using vector embeddings.

## Prerequisites

1. Make sure you have all required packages installed:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env.local` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Required Files
The script expects the following files to be present:
- `embeddings.npy`: Contains pre-computed embeddings for schemes
- `metadata.json`: Contains metadata for the schemes
- `scheme_details.json`: Contains detailed information about each scheme
- Ensure it is present in the same directory as the script.

## Running the Script

1. Open a terminal in the project directory

2. Run the script:
   ```
   python searchDb.py
   ```
   If you wish to play around with the search change the query in the searchDb.py file.
   test_queries = [
    "I am a woman entrepreneur in Delhi looking to start a small business",
    "Looking for education scholarships for SC/ST students in Maharashtra",
    "I am a self-employed farmer in Karnataka looking for subsidies for seeds and fertilizers."
   ]
    Change the above queries to test different user scenarios.

3. The script will first verify:
   - Number of vectors in FAISS
   - Number of entries in metadata
   - Number of entries in scheme details

4. You can then query the database by providing search terms related to government schemes. The script will:
   - Convert your query to embeddings
   - Find similar schemes using FAISS
   - Return relevant scheme details including:
     - Benefits
     - Application process
     - Required documents
     - Eligibility criteria

## Security Note
- Keep your `.env.local` file secure and never commit it to version control
- The `.gitignore` file is configured to exclude sensitive files

## Troubleshooting
- If you get an API key error, verify your `.env.local` file is properly configured
- Make sure all required data files are present in the correct locations
- Check that all dependencies are installed correctly

# RightScheme-AI
