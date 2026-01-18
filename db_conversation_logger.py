"""
MongoDB-backed conversation logger
"""
from datetime import datetime
from database import get_sessions_collection, get_messages_collection, init_db
import logging

logger = logging.getLogger(__name__)

class MongoConversationLogger:
    def __init__(self, session_id: str, kb_id: str, environment: str = "dev"):
        self.session_id = session_id
        self.kb_id = kb_id
        self.environment = environment
        self.start_time = datetime.utcnow()
        self.messages = []
    
    async def initialize(self):
        """Create session document in MongoDB"""
        try:
            sessions = get_sessions_collection()
            session_doc = {
                "session_id": self.session_id,
                "kb_id": self.kb_id,
                "start_time": self.start_time,
                "end_time": None,
                "duration_seconds": 0,
                "message_count": 0,
                "text_input_tokens": 0,
                "text_output_tokens": 0,
                "audio_input_tokens": 0,
                "audio_output_tokens": 0,
                "cost_usd": 0.0,
                "cost_breakdown": {},
                "environment": self.environment,
                "created_at": datetime.utcnow()
            }
            await sessions.insert_one(session_doc)
            logger.info(f"[MONGO] Created session: {self.session_id}")
        except Exception as e:
            logger.error(f"[MONGO] Failed to create session: {e}")
    
    async def log_message(self, role: str, content: str, message_type: str = "text", metadata: dict = None):
        """Log a message to MongoDB"""
        message_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "type": message_type,
            "content": content,
            "metadata": metadata or {}
        }
        self.messages.append(message_data)
        
        try:
            # Save message to messages collection
            messages = get_messages_collection()
            message_doc = {
                "session_id": self.session_id,
                "timestamp": datetime.utcnow(),
                "role": role,
                "message_type": message_type,
                "content": content,
                "metadata": metadata or {}
            }
            await messages.insert_one(message_doc)
            
            # Update session message count
            sessions = get_sessions_collection()
            await sessions.update_one(
                {"session_id": self.session_id},
                {"$inc": {"message_count": 1}}
            )
        except Exception as e:
            logger.error(f"[MONGO] Failed to log message: {e}")
    
    async def log_function_call(self, function_name: str, arguments: dict, result: str):
        """Log function call"""
        await self.log_message(
            role="function",
            content=result,
            message_type="function_call",
            metadata={"function_name": function_name, "arguments": arguments}
        )
    
    async def save(self, cost_summary: dict = None):
        """Update session with final cost and duration"""
        try:
            sessions = get_sessions_collection()
            end_time = datetime.utcnow()
            duration = (end_time - self.start_time).total_seconds()
            
            update_data = {
                "end_time": end_time,
                "duration_seconds": duration
            }
            
            if cost_summary:
                update_data.update({
                    "text_input_tokens": cost_summary['tokens']['text_input'],
                    "text_output_tokens": cost_summary['tokens']['text_output'],
                    "audio_input_tokens": cost_summary['tokens']['audio_input'],
                    "audio_output_tokens": cost_summary['tokens']['audio_output'],
                    "cost_usd": cost_summary['cost_usd'],
                    "cost_breakdown": cost_summary['cost_breakdown']
                })
            
            await sessions.update_one(
                {"session_id": self.session_id},
                {"$set": update_data}
            )
            
            logger.info(f"[MONGO] Updated session: {self.session_id}")
            return f"mongodb:{self.session_id}"
        except Exception as e:
            logger.error(f"[MONGO] Failed to save session: {e}")
            return None
