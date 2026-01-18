"""
Manual load testing script - Run this separately
Usage: python run_load_test.py <kb_id> [test_type]
"""
import asyncio
import sys
from test_load import load_test, stress_test_reconnection

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_load_test.py <kb_id> [test_type]")
        print("test_type: load (default), stress")
        sys.exit(1)
    
    kb_id = sys.argv[1]
    test_type = sys.argv[2] if len(sys.argv) > 2 else "load"
    
    if test_type == "load":
        asyncio.run(load_test(kb_id, concurrent_connections=10, duration=30))
    elif test_type == "stress":
        asyncio.run(stress_test_reconnection(kb_id, iterations=10))
    else:
        print(f"Unknown test type: {test_type}")
