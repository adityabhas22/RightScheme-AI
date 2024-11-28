from typing import List, Dict, Any
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryMemory
from langchain.tools import tool
from pydantic import BaseModel, Field
import faiss
import numpy as np
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
client = OpenAI()

# Add Streamlit session state initialization
if "scheme_agent" not in st.session_state:
    st.session_state.scheme_agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

class SchemeInfo(BaseModel):
    """Schema for scheme information"""
    scheme_name: str = Field(description="Name of the government scheme")
    details: str = Field(description="Details about the scheme")
    source_file: str = Field(description="Source file containing the information")
    relevance_score: float = Field(description="Relevance score of the retrieved information")

class SchemeTools:
    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.index, self.metadata = self._load_latest_index()
        self.current_scheme = None
        self.last_search_results = []

    def _load_latest_index(self):
        """Load the most recent FAISS index and its metadata."""
        try:
            index_files = [f for f in os.listdir(self.index_dir) if f.startswith('faiss_index_') and f.endswith('.index')]
            if not index_files:
                raise FileNotFoundError("No FAISS index files found")
            
            latest_index = max(index_files)
            index_path = os.path.join(self.index_dir, latest_index)
            
            timestamp = latest_index.replace('faiss_index_', '').replace('.index', '')
            metadata_file = f'faiss_metadata_{timestamp}.json'
            metadata_path = os.path.join(self.index_dir, metadata_file)
            
            index = faiss.read_index(index_path)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            return index, metadata
            
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            return None, None

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for query text."""
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return np.array(response.data[0].embedding, dtype='float32')
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None

    def search_scheme(self, query: str) -> List[SchemeInfo]:
        """Search for information about government schemes."""
        try:
            query_embedding = self.generate_embedding(query)
            if query_embedding is None:
                return []
            
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1), 
                3  # Get top 3 results
            )
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx != -1:
                    metadata = self.metadata[idx]
                    scheme_info = SchemeInfo(
                        scheme_name=metadata.get("scheme_name", "Unknown Scheme"),
                        details=metadata["text"],
                        source_file=metadata["source_file"],
                        relevance_score=float(1 / (1 + distance))
                    )
                    results.append(scheme_info)
            
            self.last_search_results = results
            return results
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            return []

    def get_eligibility_criteria(self, scheme_name: str) -> str:
        """Get eligibility criteria for a specific scheme."""
        query = f"eligibility criteria for {scheme_name}"
        results = self.search_scheme(query)
        if not results:
            return "No eligibility criteria found for this scheme."
        return results[0].details

    def get_required_documents(self, scheme_name: str) -> str:
        """Get required documents for a specific scheme."""
        query = f"documents required for {scheme_name}"
        results = self.search_scheme(query)
        if not results:
            return "No document information found for this scheme."
        return results[0].details

    def get_application_process(self, scheme_name: str) -> str:
        """Get detailed application process for a specific scheme."""
        query = f"application process steps procedure how to apply for {scheme_name}"
        results = self.search_scheme(query)
        if not results:
            return "No application process information found for this scheme."
        
        # Try to find the most relevant information about the application process
        application_info = results[0].details
        
        # Format the response to be more readable
        response = (
            f"Application Process for {scheme_name}:\n\n"
            f"{application_info}\n\n"
            "Note: Please verify these steps from the official website or nearest government office "
            "as procedures may be updated periodically."
        )
        return response

    def parse_eligibility_criteria(self, scheme_name: str) -> List[Dict[str, Any]]:
        """Convert eligibility criteria into structured questions."""
        query = f"eligibility criteria for {scheme_name}"
        results = self.search_scheme(query)
        
        if not results:
            return []
        
        try:
            # Simplified prompt for GPT-3.5-turbo
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Create 3-5 yes/no questions to check eligibility. Format: Q1? [yes/no required] (type: age/income/occupation/location/other)"
                    },
                    {
                        "role": "user",
                        "content": f"Eligibility criteria: {results[0].details}"
                    }
                ]
            )
            
            # Parse the simpler response format
            questions = []
            for line in response.choices[0].message.content.split('\n'):
                if '?' in line:
                    try:
                        # Extract question and metadata
                        question_part = line.split('?')[0] + '?'
                        metadata = line.split('?')[1].strip()
                        required = 'yes' in metadata.lower()
                        
                        # Extract criteria type
                        criteria_type = 'other'
                        for t in ['age', 'income', 'occupation', 'location']:
                            if t in metadata.lower():
                                criteria_type = t
                                break
                        
                        questions.append({
                            "question": question_part,
                            "required_answer": True,
                            "disqualifying": True,
                            "criteria_type": criteria_type,
                            "explanation": metadata
                        })
                    except Exception as e:
                        print(f"Error parsing question line: {str(e)}")
                        continue
            
            return questions if questions else self._generate_fallback_questions(scheme_name, results[0].details)
            
        except Exception as e:
            print(f"Error parsing eligibility criteria: {str(e)}")
            return self._generate_fallback_questions(scheme_name, results[0].details)

    def _generate_fallback_questions(self, scheme_name: str, criteria_text: str) -> List[Dict[str, Any]]:
        """Generate basic eligibility questions when parsing fails."""
        try:
            # Simple prompt to get basic yes/no questions
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Convert the eligibility criteria into 3-5 simple yes/no questions. Each question should be crucial for determining eligibility."
                    },
                    {
                        "role": "user",
                        "content": f"Eligibility criteria for {scheme_name}: {criteria_text}"
                    }
                ]
            )
            
            questions = response.choices[0].message.content.strip().split("\n")
            # Format basic questions
            return [
                {
                    "question": q.strip("1234567890. "),
                    "required_answer": True,
                    "disqualifying": True,
                    "criteria_type": "other",
                    "explanation": "Basic eligibility requirement"
                }
                for q in questions if "?" in q
            ]
        except Exception as e:
            print(f"Error generating fallback questions: {str(e)}")
            return [
                {
                    "question": f"Do you meet the basic eligibility criteria for {scheme_name}?",
                    "required_answer": True,
                    "disqualifying": True,
                    "criteria_type": "other",
                    "explanation": "Basic eligibility check"
                }
            ]

    def check_eligibility(self, scheme_name: str, answers: Dict[str, bool]) -> Dict[str, Any]:
        """Check eligibility based on user answers."""
        criteria = self.parse_eligibility_criteria(scheme_name)
        
        if not criteria:
            return {
                "eligible": None,
                "message": "Could not determine eligibility criteria for this scheme."
            }
        
        # Check for immediate disqualifiers first
        for criterion in criteria:
            question = criterion["question"]
            if question in answers:
                if criterion.get("disqualifying", False):
                    if answers[question] != criterion["required_answer"]:
                        return {
                            "eligible": False,
                            "message": f"Not eligible: {criterion.get('explanation', 'Does not meet mandatory requirement')}",
                            "failed_criteria": [criterion["question"]]
                        }
        
        # Check all other criteria
        failed_criteria = []
        for criterion in criteria:
            question = criterion["question"]
            if question in answers:
                if answers[question] != criterion["required_answer"]:
                    failed_criteria.append(criterion["question"])
        
        if failed_criteria:
            return {
                "eligible": False,
                "message": "Not eligible based on provided information.",
                "failed_criteria": failed_criteria
            }
        
        return {
            "eligible": True,
            "message": "Based on the provided information, you appear to be eligible for this scheme.",
            "next_steps": "Please proceed with the application process."
        }

def create_scheme_agent():
    # Initialize tools
    tools_instance = SchemeTools("vectorDb")
    
    # Create tools using the Tool class
    tools = [
        Tool(
            name="search_scheme",
            func=tools_instance.search_scheme,
            description="Search for information about government schemes. Use this tool when you need to find general information about schemes."
        ),
        Tool(
            name="get_eligibility_criteria",
            func=tools_instance.get_eligibility_criteria,
            description="Get eligibility criteria for a specific scheme. Use this tool when you need to find who is eligible for a scheme."
        ),
        Tool(
            name="get_required_documents",
            func=tools_instance.get_required_documents,
            description="Get required documents for a specific scheme. Use this tool when you need to find what documents are needed for a scheme."
        ),
        Tool(
            name="get_application_process",
            func=tools_instance.get_application_process,
            description="Get detailed step-by-step application process for a specific scheme. Use this tool when someone asks how to apply for a scheme or needs application procedure details."
        )
    ]

    # Initialize LLM
    llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")

    # Initialize ConversationSummaryMemory
    memory = ConversationSummaryMemory(
        llm=ChatOpenAI(temperature=0.7, model="gpt-4o-mini"),
        memory_key="chat_history",
        return_messages=True,
        max_token_limit=2000
    )

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert assistant for Indian Government Schemes. Provide detailed but well-structured information.

        Previous conversation:
        {chat_history}
        
        RESPONSE FORMAT:
        
        📋 SCHEME NAME:
        [Full name of the scheme]
        
        💡 OVERVIEW:
        [2-3 sentences explaining the scheme's purpose and main objective]
        
        💰 KEY BENEFITS:
        • [List each major benefit in detail]
        • [Include monetary values where applicable]
        • [Mention subsidies or financial assistance]
        • [Add any special benefits]
        
        🎯 ELIGIBILITY:
        • [List primary eligibility criteria]
        • [Include income limits if any]
        • [Mention target beneficiaries]
        • [Special categories if applicable]
        
        📝 HOW TO APPLY:
        1. [Step-by-step application process]
        2. [Where to apply]
        3. [Online/offline methods]
        
        📄 REQUIRED DOCUMENTS:
        • [List all necessary documents]
        • [Any special certificates needed]
        
        🏛️ SCHEME TYPE:
        • Central/State scheme
        • Implementing ministry/department
        • State-specific variations if any
        
        GUIDELINES:
        1. Keep focus on current scheme until user changes topic
        2. Use simple language but provide complete information
        3. Break down complex terms in parentheses
        4. Format information with bullet points and numbers
        5. Consider user's state context
        6. Highlight important points with emojis
        
        Remember: Make information comprehensive yet easy to read."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True
    )

    return agent_executor

def get_conversation_summary(agent: AgentExecutor) -> str:
    """Get the current conversation summary."""
    if not agent:
        return "No conversation history available."
    return str(agent.memory.load_memory_variables({})["chat_history"])

def format_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Format the agent's response for display."""
    return {
        "response": response["output"],
        "conversation_summary": get_conversation_summary(st.session_state.scheme_agent)
    }

def process_query(query: str) -> Dict[str, Any]:
    """Process a query and return the formatted response."""
    if not st.session_state.scheme_agent:
        st.session_state.scheme_agent = create_scheme_agent()
    
    response = st.session_state.scheme_agent.invoke({"input": query})
    
    # Try to identify the scheme being discussed
    try:
        scheme_name = extract_scheme_name(response["output"])
        if scheme_name:
            st.session_state.current_scheme = scheme_name
    except Exception as e:
        print(f"Error extracting scheme name: {str(e)}")
    
    return format_response(response)

def main():
    st.title("Government Schemes Assistant")
    st.write("Ask me anything about Indian Government Schemes!")

    # Initialize the agent if not already done
    if not st.session_state.scheme_agent:
        st.session_state.scheme_agent = create_scheme_agent()

    # Chat interface
    if query := st.chat_input("Type your question here..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": query})

        # Get response
        with st.spinner("Thinking..."):
            response_data = process_query(query)

        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response_data["response"]})

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Display conversation summary in expander
        with st.expander("View Conversation Summary"):
            st.write(response_data["conversation_summary"])

def extract_scheme_name(text: str) -> str:
    """Extract scheme name from response text."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract only the scheme name. Reply 'none' if no scheme found."},
                {"role": "user", "content": text}
            ]
        )
        scheme_name = response.choices[0].message.content.strip()
        return None if scheme_name.lower() == 'none' else scheme_name
    except Exception as e:
        print(f"Error extracting scheme name: {str(e)}")
        return None

# Export necessary components
__all__ = [
    'process_query',
    'create_scheme_agent',
    'SchemeTools',
    'extract_scheme_name',
    'format_response',
    'get_conversation_summary'
]

if __name__ == "__main__":
    main() 