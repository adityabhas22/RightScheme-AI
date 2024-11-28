import faiss
import numpy as np
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.memory import ConversationSummaryMemory
from langchain.schema import SystemMessage


# Load environment variables and initialize OpenAI client
load_dotenv()
client = OpenAI()


class VectorDBQuerier:
    def __init__(self, index_dir):
        """Initialize the querier with the latest index and metadata."""
        self.index_dir = index_dir
        self.index, self.metadata = self._load_latest_index()
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name="gpt-3.5-turbo"
        )
        
        # Initialize memory
        self.memory = ConversationSummaryMemory(
            llm=self.llm,
            memory_key="chat_history",
            return_messages=True,
            
        )
        
        # Create a custom prompt template for government schemes
        self.prompt = PromptTemplate(
            input_variables=["chat_history", "context", "question"],
            template="""You are an expert assistant for Indian Government Schemes.

Previous Conversation:
{chat_history}

Context Information:
{context}

Question: {question}

Instructions:
1. Consider the conversation history when providing context
2. Provide a clear and detailed answer based on the retrieved documents
3. Always mention specific scheme names when discussing them
4. Include eligibility criteria if available
5. Mention any benefits or financial assistance
6. If application process details are available, include them
7. If the information isn't in the documents, say so
8. Reference any relevant information from previous interactions if applicable

Answer: Let me help you with information about Indian Government Schemes."""
        )
        
        # Create the chain with memory
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            verbose=True
        )
    
    def _load_latest_index(self):
        """Load the most recent FAISS index and its metadata."""
        try:
            # Find the most recent index file
            index_files = [f for f in os.listdir(self.index_dir) if f.startswith('faiss_index_') and f.endswith('.index')]
            if not index_files:
                raise FileNotFoundError("No FAISS index files found")
            
            latest_index = max(index_files)
            index_path = os.path.join(self.index_dir, latest_index)
            
            # Find corresponding metadata file
            timestamp = latest_index.replace('faiss_index_', '').replace('.index', '')
            metadata_file = f'faiss_metadata_{timestamp}.json'
            metadata_path = os.path.join(self.index_dir, metadata_file)
            
            print(f"Loading index from: {index_path}")
            print(f"Loading metadata from: {metadata_path}")
            
            # Load files
            index = faiss.read_index(index_path)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            return index, metadata
            
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            return None, None
    
    def generate_embedding(self, text):
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
    
    def search(self, query_text, top_k=5):
        """Search the vector database with a text query."""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query_text)
            if query_embedding is None:
                return []
            
            # Search the index
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1), 
                top_k
            )
            
            # Format results
            results = []
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx != -1:  # Valid match
                    metadata = self.metadata[idx]
                    result = {
                        "rank": i + 1,
                        "distance": float(distance),
                        "chunk_id": metadata["chunk_id"],
                        "source_file": metadata["source_file"],
                        "text": metadata["text"]
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            return []
    
    def process_with_llm(self, query: str, search_results: list) -> dict:
        """Process search results with LangChain LLM to generate a response."""
        try:
            # Format context from search results
            context_parts = []
            for result in search_results:
                context_parts.append(
                    f"Document (from {result['source_file']}):\n{result['text']}\n"
                    f"Relevance Score: {1 / (1 + result['distance']):.4f}\n"
                )
            context = "\n\n".join(context_parts)
            
            # Get chat history
            memory_vars = self.memory.load_memory_variables({})
            chat_history = memory_vars.get("chat_history", "No previous conversation.")
            
            try:
                # Generate response using LangChain
                response = self.chain({
                    "chat_history": str(chat_history),
                    "context": context,
                    "question": query
                })["text"]  # Extract text from response
                
                # Save interaction to memory
                self.memory.save_context(
                    {"input": query},
                    {"output": response}
                )
                
                return {
                    "ai_response": response,
                    "sources": [
                        {
                            "file": r['source_file'],
                            "relevance": 1 / (1 + r['distance']),
                            "text": r['text'][:200] + "..."
                        }
                        for r in search_results
                    ],
                    "chat_history": str(chat_history)
                }
                
            except Exception as e:
                print(f"Chain execution error: {str(e)}")
                raise
                
        except Exception as e:
            print(f"Error processing with LLM: {str(e)}")
            return {
                "ai_response": "I encountered an error while processing your query.",
                "sources": [],
                "chat_history": ""
            }
    
    def format_results(self, results):
        """Format search results for display."""
        if not results:
            return "No results found."
        
        output = []
        output.append("\nSearch Results:")
        output.append("=" * 50)
        
        for result in results:
            output.append(f"\nRank: {result['rank']}")
            output.append(f"Source: {result['source_file']}")
            output.append(f"Relevance Score: {1 / (1 + result['distance']):.4f}")
            output.append("\nContent:")
            output.append("-" * 40)
            output.append(result['text'])
            output.append("-" * 40)
        
        return "\n".join(output)
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation history."""
        try:
            chat_history = self.memory.load_memory_variables({})["chat_history"]
            if not chat_history:
                return "No conversation history yet."
            return str(chat_history)
        except Exception as e:
            print(f"Error getting conversation summary: {str(e)}")
            return "Error retrieving conversation history."

def main():
    # Specify the directory containing your FAISS index
    vector_db_dir = "vectorDb"
    
    # Initialize querier
    querier = VectorDBQuerier(vector_db_dir)
    
    print("\nGovernment Schemes Query System")
    print("=" * 50)
    print("Type your query below (or 'exit' to quit, 'history' to see conversation summary)")
    
    while True:
        query = input("\nQuery: ").strip()
        
        if query.lower() == 'exit':
            print("\nConversation Summary:")
            print(querier.get_conversation_summary())
            print("\nGoodbye!")
            break
            
        if query.lower() == 'history':
            print("\nConversation History:")
            print(querier.get_conversation_summary())
            continue
        
        if not query:
            print("Please enter a valid query.")
            continue
        
        # Search vector database
        results = querier.search(query, top_k=3)
        
        if results:
            # Get AI response with sources
            response_data = querier.process_with_llm(query, results)
            
            # Display AI response
            print("\n🤖 AI Response:")
            print("=" * 50)
            print(response_data["ai_response"])
            
            # Display sources
            print("\n📚 Sources Used:")
            print("=" * 50)
            for i, source in enumerate(response_data["sources"], 1):
                print(f"\n{i}. {source['file']}")
                print(f"Relevance Score: {source['relevance']:.4f}")
                print(f"Preview: {source['text']}")
        else:
            print("No relevant information found for your query.")

if __name__ == "__main__":
    main() 