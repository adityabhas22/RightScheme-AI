
# RightScheme AI 🏛️

RightScheme AI is an intelligent platform that helps citizens discover, understand, and access government welfare schemes in India. The platform uses advanced AI technology to provide personalized scheme recommendations and detailed information about government welfare programs.

## Features 🌟

- **Semantic Search** 🔍: Ask questions about any government scheme and get detailed answers
- **Find Right Scheme** 🎯: Get personalized scheme recommendations based on your profile
- **Compare Schemes** 📊: Compare different schemes side by side to make informed decisions

## Prerequisites 📋

Before running the application, make sure you have:

- Python 3.8 or higher installed
- pip (Python package installer)
- Access to OpenAI API
- Access to Pinecone API

## Installation 🚀

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rightscheme-ai.git
   cd rightscheme-ai
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Setup ⚙️

1. Create a `.env` file in the root directory
2. Add the following environment variables:
   ```plaintext
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENV=your_pinecone_environment
   PINECONE_INDEX_NAME=your_pinecone_index_name
   ```


## Running the Application 🏃‍♂️

1. Make sure your virtual environment is activated
2. Run the Streamlit application:
   ```bash
   streamlit run Home.py
   ```

3. Open your web browser and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

## Project Structure 📁

```
rightscheme-ai/
├── Home.py                 # Main application entry point
├── pages/                  # Streamlit pages
│   ├── 1_Semantic_Search.py
│   ├── 2_Find_Right_Scheme.py
│   └── 3_Compare_Schemes.py
├── Python_Files/           # Backend logic
│   ├── scheme_agent.py
│   ├── migrate_to_pinecone.py
│   ├── test_pinecone_connection.py
│   ├── verify_pinecone_data.py
│   ├── create_vectordb.py
│   └── query_vectordb.py
├── utils/                  # Utility functions
│   └── common.py
├── requirements.txt        # Project dependencies
├── .env                    # Environment variables
└── README.md               # Project documentation
```

## Troubleshooting 🔧

If you encounter any issues:

1. Ensure all dependencies are correctly installed:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. Verify your `.env` file contains all required variables
3. Check if your API keys are valid and have sufficient credits
4. Make sure you're using a compatible Python version


