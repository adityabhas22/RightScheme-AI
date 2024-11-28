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
    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

    # Initialize ConversationSummaryMemory
    memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True,
        max_token_limit=2000
    )

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert assistant for Indian Government Schemes, helping users understand and access various government welfare programs.

        Previous conversation summary:
        {chat_history}
        
        GUIDELINES:
        1. Maintain strong conversation context:
           - Always check the previous messages to understand the ongoing discussion
           - If user asks for more information, provide details about the scheme last discussed
           - Stay focused on the current scheme until user asks about something else
        
        2. When providing scheme information:
           📋 SCHEME OVERVIEW:
           [Brief explanation of the scheme]
           
           💰 KEY BENEFITS:
           • [List main benefits in simple terms]
           • [Include monetary benefits if any]
           
           🎯 ELIGIBILITY:
           • [Who can apply]
           • [Basic requirements]
           
           📝 APPLICATION PROCESS:
           • [Step-by-step application guide]
           • [Where to apply]
           
           📄 REQUIRED DOCUMENTS:
           • [List of necessary documents]
           
           🏛️ AVAILABILITY:
           • [Central or State scheme]
           • [State-specific details if any]
        
        3. When user asks for "more information":
           - Provide application process if not shared before
           - Share document requirements if not mentioned earlier
           - Give specific details about benefits and subsidy amounts
           - Include contact information or relevant offices
        
        4. Always use simple language and explain technical terms
        5. Consider the user's state context in responses
        
        Remember: Stay focused on the current scheme being discussed until the user explicitly asks about something else.
        """),
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

if __name__ == "__main__":
    main() 