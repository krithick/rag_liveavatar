"""
Unit tests for RAG service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rag_service import DynamicRAG

@pytest.fixture
def mock_config():
    with patch('rag_service.Config') as mock:
        mock.AZURE_SEARCH_ENDPOINT = "https://test.search.windows.net"
        mock.AZURE_SEARCH_INDEX_NAME = "test-index"
        mock.AZURE_SEARCH_API_KEY = "test-key"
        mock.EMBEDDING_API_KEY = "test-key"
        mock.EMBEDDING_ENDPOINT = "https://test.openai.azure.com"
        mock.EMBEDDING_API_VERSION = "2023-05-15"
        mock.EMBEDDING_DEPLOYMENT_NAME = "test-embedding"
        yield mock

@pytest.fixture
def mock_search_client():
    with patch('rag_service.SearchClient') as mock:
        yield mock

@pytest.fixture
def mock_openai_client():
    with patch('rag_service.AzureOpenAI') as mock:
        yield mock

def test_rag_init_success(mock_config, mock_search_client, mock_openai_client):
    """Test successful RAG initialization"""
    rag = DynamicRAG()
    assert rag.search_client is not None
    assert rag.openai_client is not None

def test_rag_init_search_client_failure(mock_config, mock_search_client, mock_openai_client):
    """Test RAG initialization fails when search client fails"""
    mock_search_client.side_effect = Exception("Connection failed")
    with pytest.raises(Exception):
        DynamicRAG()

def test_search_empty_query(mock_config, mock_search_client, mock_openai_client):
    """Test search with empty query"""
    rag = DynamicRAG()
    result = rag.search("", "kb123")
    assert result is None

def test_search_empty_kb_id(mock_config, mock_search_client, mock_openai_client):
    """Test search with empty KB ID"""
    rag = DynamicRAG()
    result = rag.search("test query", "")
    assert result is None

def test_search_success(mock_config, mock_search_client, mock_openai_client):
    """Test successful search"""
    rag = DynamicRAG()
    
    # Mock embedding response
    mock_embedding = Mock()
    mock_embedding.data = [Mock(embedding=[0.1] * 1536)]
    rag.openai_client.embeddings.create = Mock(return_value=mock_embedding)
    
    # Mock search results
    mock_results = [
        {"content": "Test content 1"},
        {"content": "Test content 2"}
    ]
    rag.search_client.search = Mock(return_value=mock_results)
    
    result = rag.search("test query", "kb123")
    assert result is not None
    assert "Test content 1" in result
    assert "Test content 2" in result

def test_search_embedding_failure(mock_config, mock_search_client, mock_openai_client):
    """Test search when embedding generation fails"""
    rag = DynamicRAG()
    rag.openai_client.embeddings.create = Mock(side_effect=Exception("API error"))
    
    result = rag.search("test query", "kb123")
    assert result is None

def test_search_no_results(mock_config, mock_search_client, mock_openai_client):
    """Test search with no results"""
    rag = DynamicRAG()
    
    mock_embedding = Mock()
    mock_embedding.data = [Mock(embedding=[0.1] * 1536)]
    rag.openai_client.embeddings.create = Mock(return_value=mock_embedding)
    
    rag.search_client.search = Mock(return_value=[])
    
    result = rag.search("test query", "kb123")
    assert result is None
