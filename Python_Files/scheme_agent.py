from typing import List, Dict, Any
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryMemory
from langchain.tools import tool
from pydantic import BaseModel, Field
import numpy as np
from openai import OpenAI
from pinecone import Pinecone
import json
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url="https://api.openai.com/v1"
)

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
    def __init__(self):
        """Initialize with Pinecone."""
        try:
            # Initialize Pinecone
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            self.index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))
            self.current_scheme = None
            self.last_search_results = []
        except Exception as e:
            print(f"Error initializing Pinecone: {str(e)}")
            raise

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
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=3,
                include_metadata=True
            )
            
            formatted_results = []
            for match in results.matches:
                scheme_info = SchemeInfo(
                    scheme_name=match.metadata.get("scheme_name", "Unknown Scheme"),
                    details=match.metadata.get("text", ""),
                    source_file=match.metadata.get("source_file", ""),
                    relevance_score=float(match.score)
                )
                formatted_results.append(scheme_info)
            
            self.last_search_results = formatted_results
            return formatted_results
            
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
        
        application_info = results[0].details
        response = (
            f"Application Process for {scheme_name}:\n\n"
            f"{application_info}\n\n"
            "Note: Please verify these steps from the official website or nearest government office "
            "as procedures may be updated periodically."
        )
        return response

def create_scheme_agent():
    # Initialize tools
    tools_instance = SchemeTools()
    
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
        
        STRICT GUIDELINES:
        1. ONLY answer questions related to government schemes, welfare programs, and benefits, even if it has potential to be related to schemes do answer the question. 
        If a user asks about anything else (like general knowledge, coding, weather, etc.), 
        firmly but politely respond:
        "I am specifically designed to help with government schemes and welfare programs. 
        Please ask me about government schemes, eligibility criteria, benefits, or application processes.
        
        
        2. Maintain strong conversation context:
           - Always check the previous messages to understand the ongoing discussion
           - If user asks for more information, provide details about the scheme last discussed
           - Stay focused on the current scheme until user asks about something else
        
        3. When providing scheme information:
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
        
        4. When user asks for "more information":
           - Provide application process if not shared before
           - Share document requirements if not mentioned earlier
           - Give specific details about benefits and subsidy amounts
           - Include contact information or relevant offices
        
        5. Always use simple language and explain technical terms
        6. Consider the user's state context in responses
        
        IMPORTANT: You must ONLY engage with queries about:
        • Government schemes and programs
        • Welfare benefits
        • Eligibility criteria
        • Application processes
        • Required documents
        • Scheme-related updates or changes
        • Government subsidies and financial assistance
        
        For ANY other topic, politely redirect the user to ask about government schemes.
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