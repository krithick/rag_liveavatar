"""
Database service for storing conversation sessions
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        load_dotenv()
        self.mongo_url = os.getenv('MONGO_URL')
        self.db_name = os.getenv('MONGO_DB_NAME')
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info("[DB] Connected to MongoDB")
        except Exception as e:
            logger.error(f"[DB] Connection failed: {e}")
            raise
    
    def save_session(self, session_data: dict, folder_path: str = None) -> str:
        """Save conversation session to database"""
        try:
            # Add folder path and save timestamp
            session_data['folder_path'] = folder_path
            session_data['saved_at'] = datetime.utcnow()
            
            result = self.db.conversations.insert_one(session_data)
            logger.info(f"[DB] Session saved: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"[DB] Failed to save session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session by ID"""
        try:
            return self.db.conversations.find_one({"session_id": session_id})
        except Exception as e:
            logger.error(f"[DB] Failed to get session: {e}")
            return None
    
    def get_sessions_by_kb(self, kb_id: str) -> List[dict]:
        """Get all sessions for a knowledge base"""
        try:
            return list(self.db.conversations.find({"kb_id": kb_id}))
        except Exception as e:
            logger.error(f"[DB] Failed to get sessions: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("[DB] Connection closed")