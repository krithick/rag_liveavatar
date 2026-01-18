"""
Conversation logging for session replay and analysis
"""
import json
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ConversationLogger:
    def __init__(self, session_id: str, kb_id: str, log_dir: str = "conversations"):
        self.session_id = session_id
        self.kb_id = kb_id
        self.log_dir = log_dir
        self.start_time = datetime.utcnow()
        self.messages = []
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
    
    def log_message(self, role: str, content: str, message_type: str = "text", metadata: dict = None):
        """Log a conversation message"""
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,  # user, assistant, system, function
            "type": message_type,  # text, audio, function_call, function_result
            "content": content,
            "metadata": metadata or {}
        }
        self.messages.append(message)
    
    def log_function_call(self, function_name: str, arguments: dict, result: str):
        """Log function call and result"""
        self.log_message(
            role="function",
            content=result,
            message_type="function_call",
            metadata={
                "function_name": function_name,
                "arguments": arguments
            }
        )
    
    def log_event(self, event_type: str, data: dict):
        """Log Azure event"""
        self.log_message(
            role="system",
            content=json.dumps(data),
            message_type=event_type,
            metadata={"event": event_type}
        )
    
    def save(self, cost_summary: dict = None):
        """Save conversation to file"""
        filename = f"{self.session_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        conversation_data = {
            "session_id": self.session_id,
            "kb_id": self.kb_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "message_count": len(self.messages),
            "messages": self.messages,
            "cost": cost_summary
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            logger.info(f"[CONVO] Saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"[CONVO] Failed to save: {e}")
            return None
    
    def get_summary(self) -> dict:
        """Get conversation summary"""
        user_messages = [m for m in self.messages if m["role"] == "user"]
        assistant_messages = [m for m in self.messages if m["role"] == "assistant"]
        function_calls = [m for m in self.messages if m["role"] == "function"]
        
        return {
            "session_id": self.session_id,
            "kb_id": self.kb_id,
            "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "total_messages": len(self.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "function_calls": len(function_calls)
        }
