"""
Environment-based configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ENV = os.getenv("ENVIRONMENT", "dev")
    
    # Azure OpenAI Realtime
    AZURE_RESOURCE = os.getenv("AZURE_RESOURCE")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    
    # Azure Search
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
    
    # Embeddings
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
    EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT")
    EMBEDDING_API_VERSION = os.getenv("EMBEDDING_API_VERSION")
    EMBEDDING_DEPLOYMENT_NAME = os.getenv("EMBEDDING_DEPLOYMENT_NAME")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8003"))
    
    # Timeouts
    AZURE_CONNECTION_TIMEOUT = int(os.getenv("AZURE_CONNECTION_TIMEOUT", "10"))
    CLIENT_INIT_TIMEOUT = int(os.getenv("CLIENT_INIT_TIMEOUT", "30"))
    
    # Resilience
    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
    RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "10.0"))
    AZURE_CIRCUIT_FAILURE_THRESHOLD = int(os.getenv("AZURE_CIRCUIT_FAILURE_THRESHOLD", "5"))
    AZURE_CIRCUIT_TIMEOUT = int(os.getenv("AZURE_CIRCUIT_TIMEOUT", "60"))
    RAG_CIRCUIT_FAILURE_THRESHOLD = int(os.getenv("RAG_CIRCUIT_FAILURE_THRESHOLD", "3"))
    RAG_CIRCUIT_TIMEOUT = int(os.getenv("RAG_CIRCUIT_TIMEOUT", "30"))
    
    @classmethod
    def validate(cls):
        required = [
            "AZURE_RESOURCE", "AZURE_OPENAI_DEPLOYMENT_NAME", "AZURE_OPENAI_API_KEY",
            "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_INDEX_NAME", "AZURE_SEARCH_API_KEY",
            "EMBEDDING_API_KEY", "EMBEDDING_ENDPOINT", "EMBEDDING_API_VERSION", "EMBEDDING_DEPLOYMENT_NAME"
        ]
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing config: {', '.join(missing)}")
