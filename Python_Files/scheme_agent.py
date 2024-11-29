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
            
            # Cache for embeddings
            self.embedding_cache = {}
            
            # Pre-compute concept embeddings
            self.concepts = {
                "financial": ["loan", "money", "fund", "finance", "credit", "subsidy"],
                "education": ["study", "school", "college", "education", "learning"],
                "health": ["medical", "health", "treatment", "hospital", "disease"],
                "employment": ["job", "work", "employment", "business", "career"],
                "housing": ["house", "home", "shelter", "residence", "building"]
            }
            self._precompute_concept_embeddings()
            
        except Exception as e:
            print(f"Error initializing Pinecone: {str(e)}")
            raise

    def _precompute_concept_embeddings(self):
        """Precompute embeddings for all concept terms."""
        self.concept_embeddings = {}
        all_terms = set(chain.from_iterable(self.concepts.values()))
        
        # Batch embedding generation
        responses = client.embeddings.create(
            input=list(all_terms),
            model="text-embedding-ada-002"
        )
        
        # Store embeddings in cache
        for term, embedding_data in zip(all_terms, responses.data):
            self.embedding_cache[term] = np.array(embedding_data.embedding, dtype='float32')

    def set_user_state(self, state: str):
        """Set the user's state for context-aware searching."""
        self.user_state = state

    def is_scheme_applicable(self, scheme_info: SchemeInfo) -> bool:
        """Check scheme applicability considering both state and central schemes."""
        if not self.user_state:
            return True
        
        scheme_details = scheme_info.details.lower()
        state_name = self.user_state.lower()
        
        # Get user's gender from session state
        user_gender = st.session_state.get('user_responses', {}).get('gender', '').lower()
        
        # Gender exclusion logic
        if user_gender:
            if user_gender == 'male' and any(phrase in scheme_details for phrase in [
                "only for women", "women only", "exclusively for women",
                "female candidates only", "women beneficiaries only"
            ]):
                return False
            
            if user_gender == 'female' and any(phrase in scheme_details for phrase in [
                "only for men", "men only", "exclusively for men",
                "male candidates only", "male beneficiaries only"
            ]):
                return False
        
        # Check if it's a central scheme
        central_indicators = {
            "central scheme", "centrally sponsored", "nationwide",
            "all states", "pan india", "government of india",
            "ministry of", "central government", "union government",
            "national scheme", "bharat", "indian government"
        }
        
        # If it's a central scheme, it's applicable
        if any(indicator in scheme_details for indicator in central_indicators):
            return True
        
        # If it specifically mentions the user's state, it's applicable
        if state_name in scheme_details:
            return True
        
        # Check if it's explicitly for another state
        indian_states = {"andhra pradesh", "arunachal pradesh", "assam", "bihar", 
                        "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh", 
                        "jharkhand", "karnataka", "kerala", "madhya pradesh", 
                        "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland", 
                        "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", 
                        "telangana", "tripura", "uttar pradesh", "uttarakhand", 
                        "west bengal"}
        
        # Only exclude if explicitly mentioned for another state
        for state in indian_states:
            if state != state_name and f"for {state}" in scheme_details:
                return False
        
        # If no explicit state restriction is found, include the scheme
        # This ensures we don't miss central schemes that don't explicitly mention their scope
        return True

    def get_question_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching."""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
            
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            embedding = np.array(response.data[0].embedding, dtype='float32')
            self.embedding_cache[text] = embedding
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None

    def search_scheme(self, query: str) -> List[SchemeInfo]:
        """Search for both state-specific and central schemes."""
        try:
            # Get embedding for original query
            query_embedding = self.get_question_embedding(query)
            if query_embedding is None:
                return []
            
            # Get results with original query
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=30,  # Increased to ensure we catch enough schemes
                include_metadata=True
            )
            
            schemes = []
            seen_schemes = set()
            
            for match in results.matches:
                if match.score >= self.MIN_RELEVANCE_SCORE:
                    scheme_info = SchemeInfo(
                        scheme_name=match.metadata.get("scheme_name", "Unknown Scheme"),
                        details=match.metadata.get("text", ""),
                        source_file=match.metadata.get("source_file", ""),
                        relevance_score=float(match.score)
                    )
                    
                    # Skip duplicates
                    if scheme_info.scheme_name in seen_schemes:
                        continue
                    
                    scheme_details = scheme_info.details.lower()
                    
                    # Check if it's a central scheme
                    is_central = any(indicator in scheme_details for indicator in [
                        "central scheme", "centrally sponsored", "nationwide",
                        "all states", "pan india", "government of india",
                        "ministry of", "central government", "union government",
                        "national scheme", "bharat", "indian government"
                    ])
                    
                    # Check if it's for user's state
                    is_state_specific = self.user_state.lower() in scheme_details
                    
                    # Include if it's either central or for user's state
                    if is_central or is_state_specific:
                        # Boost score for exact state match
                        if is_state_specific:
                            scheme_info.relevance_score = min(1.0, scheme_info.relevance_score + 0.1)
                        
                        schemes.append(scheme_info)
                        seen_schemes.add(scheme_info.scheme_name)
            
            # Sort by relevance and return top results
            schemes.sort(key=lambda x: x.relevance_score, reverse=True)
            return schemes[:5]
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            return []

    def diversify_results(self, results: List[SchemeInfo]) -> List[SchemeInfo]:
        """Ensure diversity in search results."""
        if not results:
            return []
            
        diversified = [results[0]]  # Start with highest scoring result
        remaining = results[1:]
        
        while remaining and len(diversified) < 5:
            # Find the result that's most different from current selections
            max_diff_score = -1
            max_diff_idx = 0
            
            for i, result in enumerate(remaining):
                min_similarity = float('inf')
                result_embedding = self.get_question_embedding(result.details)
                
                if result_embedding is None:
                    continue
                    
                # Calculate minimum similarity to already selected results
                for selected in diversified:
                    selected_embedding = self.get_question_embedding(selected.details)
                    if selected_embedding is not None:
                        similarity = np.dot(result_embedding, selected_embedding) / (
                            np.linalg.norm(result_embedding) * np.linalg.norm(selected_embedding)
                        )
                        min_similarity = min(min_similarity, similarity)
                
                # Higher difference score means more diverse
                diff_score = 1 - min_similarity
                if diff_score > max_diff_score:
                    max_diff_score = diff_score
                    max_diff_idx = i
            
            # Add most diverse result to selection
            diversified.append(remaining.pop(max_diff_idx))
        
        return diversified

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

    def is_similar_question(self, query: str, base_questions: List[str], threshold: float = 0.85) -> bool:
        """Check if query is semantically similar to any base question."""
        query_embedding = self.get_question_embedding(query)
        if query_embedding is None:
            return False
        
        for base_q in base_questions:
            base_embedding = self.get_question_embedding(base_q)
            if base_embedding is None:
                continue
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, base_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(base_embedding)
            )
            
            if similarity >= threshold:
                return True
        
        return False

    def is_allowed_question(self, query: str, chat_history: List[Dict[str, str]]) -> tuple[bool, str]:
        """
        Check if the query is allowed using semantic similarity.
        Returns (is_allowed, response_if_not_allowed)
        """
        # Base questions for semantic comparison
        base_questions = [
            "who made you",
            "what is your purpose",
            "how can you help me"
        ]
        
        # Convert query to lowercase for processing
        query_lower = query.lower()
        
        # Check if query is semantically similar to allowed questions
        if self.is_similar_question(query_lower, base_questions):
            return True, ""
        
        # Check if query is about government schemes
        scheme_related_terms = {
            "scheme", "yojana", "program", "benefit", "welfare", "subsidy", "grant",
            "application", "apply", "document", "eligibility", "criteria", "government",
            "qualification", "income", "category", "reservation"
        }
        
        if any(term in query_lower for term in scheme_related_terms):
            return True, ""
        
        # If not allowed, return contextual redirect
        return False, get_contextual_redirect(query, chat_history)

    def validate_response(self, response: str) -> tuple[bool, str]:
        """Validate response for potential inaccuracies."""
        red_flags = [
            "might be", "probably", "I think", "should be",
            "around", "approximately", "possibly"
        ]
        
        has_red_flags = any(flag in response.lower() for flag in red_flags)
        
        if has_red_flags:
            return False, (
                f"{response}\n\n"
                "⚠️ Note: Some details in this response may need verification. "
                "Please confirm with official government sources."
            )
        
        return True, response

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

    # Initialize LLM - using only gpt-4o-mini
    llm = ChatOpenAI(
        temperature=0.7,
        model="gpt-4o-mini",  # Enforcing use of gpt-4o-mini
        model_kwargs={"top_p": 0.9}  # Optional: add any specific model parameters
    )

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
        1. ONLY answer questions related to government schemes, welfare programs, and benefits.
        
        2. For questions about who created you or your purpose:
           - Respond: "I am an AI assistant created by the government to help citizens find and understand various government schemes and welfare programs."
           - Keep responses focused on your role in helping with government schemes
           - Do not discuss technical details about your creation or operation
        
        3. When users say "yes" or give short responses:
           - Always maintain context from previous messages
           - Ask follow-up questions to clarify their needs
           - Guide them towards specific scheme information
        
        4. Stay focused on government schemes:
           - If users ask about non-scheme topics, politely redirect them
           - Always bring the conversation back to available schemes and benefits
           - Provide specific, actionable information about schemes
        
        5. Handle gender-specific schemes appropriately:
           - Only exclude schemes explicitly marked for other genders
           - Include all generally applicable schemes
           - Be inclusive in language and recommendations
        
        IMPORTANT: You must ONLY engage with:
        • Government schemes and programs
        • Welfare benefits and eligibility
        • Application processes and documents
        • Basic questions about your purpose
        
        For ANY other topic, politely redirect to scheme-related discussions.
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

def get_conversation_context(chat_history: List[Dict[str, str]]) -> tuple[str, str]:
    """
    Analyze chat history to extract the most recent scheme and conversation context.
    Returns (last_scheme, conversation_topic)
    """
    last_scheme = ""
    conversation_topic = ""
    
    # Look through recent messages (in reverse)
    for message in reversed(chat_history):
        content = message['content'].lower()
        
        # Look for scheme names (usually followed by "scheme" or "yojana")
        scheme_match = re.search(r'([a-zA-Z\s]+)(scheme|yojana)', content)
        if scheme_match and not last_scheme:
            last_scheme = scheme_match.group(1).strip()
        
        # Look for conversation topics
        topics = ["eligibility", "documents", "application", "benefits"]
        for topic in topics:
            if topic in content and not conversation_topic:
                conversation_topic = topic
                break
        
        if last_scheme and conversation_topic:
            break
    
    return last_scheme, conversation_topic

def get_contextual_redirect(query: str, chat_history: List[Dict[str, str]]) -> str:
    """Generate a context-aware redirection message."""
    last_scheme, conversation_topic = get_conversation_context(chat_history)
    
    if last_scheme:
        if conversation_topic:
            return (
                f"I see you're interested in {last_scheme}. While I can't help with {query}, "
                f"I can tell you more about the {conversation_topic} requirements or other aspects of this scheme. "
                f"What specific information would you like to know?"
            )
        return (
            f"Let's focus on helping you with the {last_scheme}. "
            f"Would you like to know about its eligibility criteria, benefits, or how to apply?"
        )
    
    if len(chat_history) > 0:
        return (
            "I'm your government schemes assistant, so I can best help you with finding and understanding "
            "various welfare programs and benefits. What kind of government assistance are you looking for?"
        )
    
    return (
        "I specialize in helping you find and understand government schemes that might benefit you. "
        "Would you like to explore available schemes based on your eligibility, or learn about specific programs?"
    )

def process_query(query: str) -> Dict[str, Any]:
    """Process a query with enhanced usage control and debugging."""
    if not st.session_state.scheme_agent:
        st.session_state.scheme_agent = create_scheme_agent()
    
    # Create SchemeTools instance if not exists
    if not hasattr(st.session_state, 'scheme_tools'):
        st.session_state.scheme_tools = SchemeTools()
    
    # Debug original query
    print("\n=== Query Processing Debug ===")
    print(f"Original Query: {query}")
    
    # Check if query is allowed with context
    is_allowed, response = st.session_state.scheme_tools.is_allowed_question(
        query, 
        st.session_state.chat_history
    )
    
    if not is_allowed:
        print(f"Query not allowed. Redirect response: {response}")
        return {
            "response": response,
            "conversation_summary": get_conversation_summary(st.session_state.scheme_agent)
        }
    
    # Handle whitelisted questions about the AI
    if any(q in query.lower() for q in ["who made you", "who created you", "what is your purpose"]):
        print("Query identified as AI purpose question")
        return {
            "response": (
                "I am an AI assistant created by the government to help citizens find and understand "
                "various government schemes and welfare programs. My purpose is to make it easier for "
                "you to discover schemes you're eligible for and guide you through the application process."
            ),
            "conversation_summary": get_conversation_summary(st.session_state.scheme_agent)
        }
    
    # Process regular scheme-related query
    print(f"Processing scheme-related query...")
    print(f"Current state: {st.session_state.user_state}")
    print(f"Chat history length: {len(st.session_state.chat_history)}")
    
    # Debug the agent invocation
    print("\n=== Agent Invocation ===")
    print(f"Final query being passed to agent: {query}")
    response = st.session_state.scheme_agent.invoke(
        {"input": query},
        callbacks=[
            LangChainCallbackHandler(
                print_input=True,  # Print input to agent
                print_output=True,  # Print output from agent
                print_intermediate_steps=True  # Print tool usage
            )
        ]
    )
    print("=== End Agent Invocation ===\n")
    
    # Validate response before returning
    is_valid, validated_response = st.session_state.scheme_tools.validate_response(response["output"])
    response["output"] = validated_response
    
    return format_response(response)

# Add LangChain callback handler for debugging
class LangChainCallbackHandler:
    def __init__(self, print_input=True, print_output=True, print_intermediate_steps=True):
        self.print_input = print_input
        self.print_output = print_output
        self.print_intermediate_steps = print_intermediate_steps
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        if self.print_input:
            print(f"\nChain Input: {inputs}")
    
    def on_chain_end(self, outputs, **kwargs):
        if self.print_output:
            print(f"\nChain Output: {outputs}")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        if self.print_intermediate_steps:
            print(f"\nTool Used: {serialized['name']}")
            print(f"Tool Input: {input_str}")
    
    def on_tool_end(self, output, **kwargs):
        if self.print_intermediate_steps:
            print(f"Tool Output: {output}")

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