from typing import List, Dict, Any, Set
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
import re
from itertools import chain
from langdetect import detect

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
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            self.index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))
            self.current_scheme = None
            self.last_search_results = []
            # Define minimum relevance score threshold
            self.MIN_RELEVANCE_SCORE = 0.7
            # Add state context
            self.user_state = None
        except Exception as e:
            print(f"Error initializing Pinecone: {str(e)}")
            raise

    def set_user_state(self, state: str):
        """Set the user's state for context-aware searching."""
        self.user_state = state

    def is_scheme_applicable(self, scheme_info: SchemeInfo) -> bool:
        """Check if a scheme is applicable based on state context."""
        if not self.user_state:
            return True
            
        scheme_details = scheme_info.details.lower()
        state_name = self.user_state.lower()
        
        # Always include central schemes
        if any(term in scheme_details for term in [
            "central scheme", 
            "centrally sponsored", 
            "nationwide",
            "all states",
            "pan india",
            "government of india"
        ]):
            return True
            
        # Include state-specific schemes
        if state_name in scheme_details:
            return True
            
        # Exclude schemes explicitly mentioning other states
        indian_states = {"andhra pradesh", "arunachal pradesh", "assam", "bihar", 
                        "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh", 
                        "jharkhand", "karnataka", "kerala", "madhya pradesh", 
                        "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland", 
                        "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", 
                        "telangana", "tripura", "uttar pradesh", "uttarakhand", 
                        "west bengal"}
        
        for state in indian_states:
            if state != state_name and state in scheme_details:
                return False
                
        return True

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

    def generate_query_variations(self, query: str) -> List[str]:
        """Generate semantic variations of the search query."""
        # Basic query variations
        variations = [query]
        
        # Add common Indian government scheme terms
        if "loan" in query.lower():
            variations.extend([
                query + " yojana",
                query.replace("loan", "credit") + " scheme",
                query.replace("loan", "financial assistance")
            ])
        
        if "farmer" in query.lower() or "agriculture" in query.lower():
            variations.extend([
                query + " kisan",
                query.replace("farmer", "agricultural") + " scheme",
                "krishi " + query
            ])
        
        # Add more variations for other common themes
        if "women" in query.lower():
            variations.extend([
                query + " mahila",
                query.replace("women", "female empowerment")
            ])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variations))

    def deduplicate_results(self, results: List[SchemeInfo]) -> List[SchemeInfo]:
        """Remove duplicate or very similar results."""
        unique_results = []
        seen_content = set()
        
        for result in results:
            # Create a simplified content fingerprint
            content_simple = re.sub(r'\s+', ' ', result.details.lower())
            content_simple = content_simple[:100]  # Compare first 100 chars
            
            if content_simple not in seen_content:
                seen_content.add(content_simple)
                unique_results.append(result)
        
        return unique_results

    def search_scheme(self, query: str) -> List[SchemeInfo]:
        """Enhanced search with state-aware filtering."""
        try:
            # Get user state from Streamlit session state
            if "user_state" in st.session_state:
                self.set_user_state(st.session_state.user_state)

            query_variations = self.generate_query_variations(query)
            all_results = []
            
            for variation in query_variations:
                query_embedding = self.generate_embedding(variation)
                if query_embedding is None:
                    continue
                
                results = self.index.query(
                    vector=query_embedding.tolist(),
                    top_k=15,  # Increased to account for filtering
                    include_metadata=True
                )
                
                for match in results.matches:
                    if match.score >= self.MIN_RELEVANCE_SCORE:
                        scheme_info = SchemeInfo(
                            scheme_name=match.metadata.get("scheme_name", "Unknown Scheme"),
                            details=match.metadata.get("text", ""),
                            source_file=match.metadata.get("source_file", ""),
                            relevance_score=float(match.score)
                        )
                        # Only add applicable schemes
                        if self.is_scheme_applicable(scheme_info):
                            all_results.append(scheme_info)
            
            # Deduplicate and sort results
            unique_results = self.deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            self.last_search_results = unique_results
            
            # Return top results
            return unique_results[:5]
            
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

class SelectiveConversationMemory(ConversationSummaryMemory):
    """A memory class that selectively retains important parts of conversations."""
    
    def _get_important_parts(self, text: str) -> bool:
        """Determine if a conversation part is important enough to retain."""
        important_indicators = [
            "scheme",
            "eligibility",
            "documents",
            "apply",
            "benefit",
            "criteria",
            "requirement",
            "process",
            "subsidy",
            "assistance",
            "welfare",
            "income",
            "category",
            "deadline",
        ]
        
        # Check if the text contains any important indicators
        return any(indicator in text.lower() for indicator in important_indicators)
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from this conversation to buffer. Override to filter."""
        input_str = inputs['input']
        output_str = outputs['output']
        
        # Only save if either input or output contains important information
        if self._get_important_parts(input_str) or self._get_important_parts(output_str):
            super().save_context(inputs, outputs)

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
    llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")

    # Initialize SelectiveConversationMemory
    memory = SelectiveConversationMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True,
        max_token_limit=2000
    )

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a friendly and helpful assistant specializing in Indian Government Schemes. While your main expertise is helping users understand and access various government welfare programs, you can also engage in casual conversation.

        You will detect the language of the user's query and respond in the same language.

        Previous conversation summary:
        {chat_history}
        CONVERSATION STYLE:
        - Be warm and approachable
        - Feel free to engage in basic greetings and small talk
        - When users ask about your capabilities, explain that you're an AI assistant focused on helping them understand government schemes
        - You can have casual conversations but gently guide users towards scheme-related information when appropriate
        
        STRICT LANGUAGE RULES:
        - Always respond in English, regardless of the language of the user query
        - Never respond in any Indian language directly; instead, always include English transliteration
        

        RESPONSE GUIDELINES:
        
        1. LANGUAGE HANDLING:
           - Detect the language of the user's query
           - Respond in the same language as the user
           - For regional languages, use both the regional script and English transliteration when mentioning scheme names
        
        2. For COMPLETELY UNRELATED requests (like coding, weather, sports):
           Respond with (in the user's language): "I apologize, but I am specifically designed to help with Indian government schemes and welfare programs. I cannot assist with [mention their request]. However, I'd be happy to help you learn about government schemes that might be relevant to your needs."
        
        3. For PARTIALLY RELATED topics (like jobs, education, business, healthcare):
           - Acknowledge their question politely
           - Bridge to relevant government schemes
           - Use previous conversation context for meaningful connections
           
           Examples:
           • Jobs: "While I can't help with general job searching, I can tell you about government schemes for employment and skill development..."
           • Education: "Although I can't provide general education advice, let me share some government schemes that offer educational support..."
           • Business: "While I can't give business advice, there are several government schemes for entrepreneurs that might interest you..."
        
        4. When providing scheme information:
           📋 SCHEME OVERVIEW:
           [Brief explanation of the scheme]
           
           💰 KEY BENEFITS:
           • [List main benefits in simple terms]
           • [Include monetary benefits if any]
           
           🎯 ELIGIBILITY:
           • [Who can apply]
           • [Basic requirements]
        
        5. For follow-up questions:
           - Provide application process details
           - Share document requirements
           - Give specific benefits information
           - Include relevant contact details
        
        6. Always use simple language and explain technical terms
        7. Consider the user's state context in responses
        
        FOCUS AREAS:
        • Government schemes and programs
        • Welfare benefits
        • Eligibility criteria
        • Application processes
        • Required documents
        • Scheme-related updates
        • Government subsidies and financial assistance
        
        Remember: 
        - Always respond in the same language as the user's query
        - For completely unrelated topics, be direct but polite in declining assistance
        - For partially related topics, find ways to connect to relevant schemes
        - When using regional languages, include scheme names in both regional script and English
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
    try:
        if not st.session_state.find_schemes["scheme_agent"]:
            st.session_state.find_schemes["scheme_agent"] = create_scheme_agent()
        
        response = st.session_state.find_schemes["scheme_agent"].invoke({"input": query})
        return {
            "response": response["output"],
            "conversation_summary": get_conversation_summary(st.session_state.find_schemes["scheme_agent"])
        }
    except Exception as e:
        return {
            "response": f"I apologize, but I encountered an error: {str(e)}",
            "conversation_summary": ""
        }

async def get_scheme_response(schemes_data):
    # Remove existing response formatting
    response = ""
    
    for scheme in schemes_data:
        response += f"📋 {scheme['name']}\n\n"
        
        response += "KEY BENEFITS:\n"
        for benefit in scheme['benefits']:
            response += f"• {benefit}\n"
        response += "\n"
        
        response += "ELIGIBILITY:\n"
        for eligibility in scheme['eligibility']:
            response += f"• {eligibility}\n"
        response += "\n---\n\n"
    
    return response

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
