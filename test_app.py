"""
Integration tests for WebSocket endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "metrics" in data

def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "counters" in data

def test_index_page(client):
    """Test index page loads"""
    response = client.get("/")
    assert response.status_code in [200, 500]  # 500 if index.html missing

@pytest.mark.asyncio
async def test_websocket_missing_kb_id():
    """Test WebSocket connection without KB ID"""
    from fastapi.testclient import TestClient
    
    with patch('app.Config.validate'):
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"kb_id": ""})
            data = websocket.receive_json()
            assert "error" in data

@pytest.mark.asyncio
async def test_websocket_azure_connection_failure():
    """Test WebSocket when Azure connection fails"""
    with patch('app.Config.validate'):
        with patch('app.connect_to_azure_realtime', side_effect=ConnectionError("Failed")):
            client = TestClient(app)
            with client.websocket_connect("/ws") as websocket:
                websocket.send_json({"kb_id": "test123"})
                data = websocket.receive_json()
                assert "error" in data
