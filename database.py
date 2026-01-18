"""
MongoDB connection and models
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "rag_liveavatar")

client = None
db = None

def get_database():
    """Get MongoDB database instance"""
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[MONGO_DB_NAME]
        logger.info(f"[MONGO] Connected to {MONGO_DB_NAME}")
    return db

# Collections
def get_sessions_collection():
    return get_database()["sessions"]

def get_messages_collection():
    return get_database()["messages"]

async def init_db():
    """Initialize database indexes"""
    try:
        sessions = get_sessions_collection()
        messages = get_messages_collection()
        
        # Create indexes
        await sessions.create_index("session_id", unique=True)
        await sessions.create_index("kb_id")
        await sessions.create_index("created_at")
        await messages.create_index("session_id")
        await messages.create_index("timestamp")
        
        logger.info("[MONGO] Indexes created")
    except Exception as e:
        logger.error(f"[MONGO] Failed to create indexes: {e}")
