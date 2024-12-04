import json
import os
from datetime import datetime
from typing import Dict, Any
import uuid

class ConversationLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            os.makedirs(os.path.join(self.log_dir, "semantic_search"))
            os.makedirs(os.path.join(self.log_dir, "find_schemes"))

    def log_conversation(self, 
                        conversation_type: str,  # 'semantic_search' or 'find_schemes'
                        user_query: str,
                        response: str,
                        metadata: Dict[str, Any] = None):
        """Log a conversation exchange to JSON file."""
        try:
            timestamp = datetime.now().isoformat()
            conversation_id = str(uuid.uuid4())
            
            log_entry = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "type": conversation_type,
                "user_query": user_query,
                "response": response,
                "metadata": metadata or {}
            }
            
            # Create filename with date
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}_conversations.json"
            filepath = os.path.join(self.log_dir, conversation_type, filename)
            
            # Read existing logs or create new list
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            else:
                logs = []
            
            # Append new log entry
            logs.append(log_entry)
            
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error logging conversation: {str(e)}")

    def log_error(self, component: str, error: str, metadata: Dict = None):
        """Log errors with context."""
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error": str(error),
            "metadata": metadata or {}
        }
        # Add logging implementation

# Global logger instance
logger = ConversationLogger() 