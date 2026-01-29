"""
Dynamic RAG service with Azure AI Search
"""
import os
from typing import List, Dict, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from openai import AzureOpenAI
from config import Config
from resilience import retry_sync, rag_circuit
import logging

logger = logging.getLogger(__name__)

class DynamicRAG:
    def __init__(self):
        try:
            self.search_client = SearchClient(
                endpoint=Config.AZURE_SEARCH_ENDPOINT,
                index_name=Config.AZURE_SEARCH_INDEX_NAME,
                credential=AzureKeyCredential(Config.AZURE_SEARCH_API_KEY)
            )
        except Exception as e:
            logger.error(f"Failed to initialize search client: {e}")
            raise
        
        try:
            self.openai_client = AzureOpenAI(
                api_key=Config.EMBEDDING_API_KEY,
                azure_endpoint=Config.EMBEDDING_ENDPOINT,
                api_version=Config.EMBEDDING_API_VERSION
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def search(self, query: str, kb_id: str, top_k: int = 5) -> Optional[str]:
        """Search KB and return formatted context with retry"""
        if not query or not kb_id:
            logger.warning("[RAG] Empty query or KB ID")
            return None
        
        logger.info(f"[RAG] Searching: {query[:50]}... in KB: {kb_id}")
        
        def _search():
            # Generate embedding
            embedding_response = self.openai_client.embeddings.create(
                input=[query],
                model=Config.EMBEDDING_DEPLOYMENT_NAME
            )
            embedding = embedding_response.data[0].embedding
            
            # Search with both kb_ prefix variants
            for kb_variant in [f"kb_{kb_id}", kb_id]:
                try:
                    results = self.search_client.search(
                        search_text=query,
                        vector_queries=[{
                            "kind": "vector",
                            "vector": embedding,
                            "fields": "contentVector",
                            "k": top_k
                        }],
                        filter=f"knowledge_base_id eq '{kb_variant}'",
                        select=["content"],
                        top=top_k
                    )
                    
                    chunks = [r["content"] for r in results]  # Increased from 400 to 800 chars
                    if chunks:
                        logger.info(f"[RAG] Found {len(chunks)} chunks")
                        return "\n\n".join(f"{c}" for c in chunks)  # More readable format
                except AzureError as e:
                    logger.error(f"[RAG] Search failed for {kb_variant}: {e}")
                    continue
            
            logger.info("[RAG] No results found")
            return None
        
        try:
            # Use circuit breaker and retry
            return rag_circuit.call(
                lambda: retry_sync(
                    _search,
                    max_attempts=Config.MAX_RETRY_ATTEMPTS,
                    base_delay=Config.RETRY_BASE_DELAY,
                    max_delay=Config.RETRY_MAX_DELAY
                )
            )
        except Exception as e:
            logger.error(f"[RAG] Search failed after retries: {e}")
            return None
