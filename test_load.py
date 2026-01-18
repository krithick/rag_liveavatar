"""
Load testing script for resilience validation
"""
import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_connection(kb_id: str, duration: int = 10):
    """Test single WebSocket connection"""
    uri = "ws://localhost:8003/ws"
    start_time = time.time()
    
    try:
        async with websockets.connect(uri) as ws:
            # Send KB ID
            await ws.send(json.dumps({"kb_id": kb_id}))
            
            # Configure session
            await ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text"],
                    "instructions": "Test connection"
                }
            }))
            
            # Keep connection alive
            while time.time() - start_time < duration:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    print(f"[{datetime.now().isoformat()}] Received: {len(message)} bytes")
                except asyncio.TimeoutError:
                    continue
            
            return True
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

async def load_test(kb_id: str, concurrent_connections: int = 10, duration: int = 30):
    """Run load test with multiple concurrent connections"""
    print(f"Starting load test: {concurrent_connections} connections for {duration}s")
    
    tasks = [test_connection(kb_id, duration) for _ in range(concurrent_connections)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if r is True)
    failed = len(results) - successful
    
    print(f"\n=== Load Test Results ===")
    print(f"Total connections: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(results)*100:.1f}%")

async def stress_test_reconnection(kb_id: str, iterations: int = 5):
    """Test reconnection resilience"""
    print(f"Starting reconnection stress test: {iterations} iterations")
    
    for i in range(iterations):
        print(f"\n[Iteration {i+1}/{iterations}]")
        try:
            success = await test_connection(kb_id, duration=5)
            print(f"Result: {'SUCCESS' if success else 'FAILED'}")
            await asyncio.sleep(2)  # Brief pause between iterations
        except Exception as e:
            print(f"Error: {e}")

# test_load.py is not a unit test - it's a manual load testing script
# Run it manually: python test_load.py <kb_id> load
