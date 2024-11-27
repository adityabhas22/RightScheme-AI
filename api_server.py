from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query_vectordb import VectorDBQuerier
from typing import List, Optional

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the querier (adjust the path as needed)
vector_db_dir = "/Users/adityabhaskara/Coding Projects/Jupyter Labs/Experimenting/vectorDb"
querier = VectorDBQuerier(vector_db_dir)

class ChatMessage(BaseModel):
    text: str

@app.post("/api/chat")
async def chat(message: ChatMessage):
    try:
        # Search vector database
        results = querier.search(message.text, top_k=3)
        
        if not results:
            return {
                "message": {
                    "id": 0,
                    "text": "I couldn't find any relevant information for your query.",
                    "sender": "ai"
                }
            }
        
        # Process with LLM
        response_data = querier.process_with_llm(message.text, results)
        
        return {
            "message": {
                "id": 0,  # Frontend will assign proper ID
                "text": response_data["ai_response"],
                "sender": "ai",
                "sources": response_data["sources"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversation-history")
async def get_history():
    try:
        history = querier.get_conversation_summary()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 